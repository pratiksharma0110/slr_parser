from collections import OrderedDict
import matplotlib
import os
import uuid

matplotlib.use('Agg')
from utils.diagram_utils import generate_dfa_diagram_image  

class SLRParser:
    def __init__(self):
        self.grammar = {}
        self.augmented_grammar = {}
        self.start_symbol = None
        self.original_start = None
        self.terminals = set(['$'])
        self.non_terminals = set()
        self.first_sets = {}
        self.follow_sets = {}
        self.states = []
        self.dfa_transitions = {}
        self.parsing_table = {'ACTION': {}, 'GOTO': {}}
        self.productions = []
        self.conflicts = []

    def parse_grammar(self, grammar_text):
        self.grammar = OrderedDict()
        self.conflicts = []
        lines = grammar_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            line = line.replace('→', '->').replace('=>', '->')
            if '->' not in line:
                continue
            left, right = line.split('->', 1)
            left = left.strip()
            right = right.strip()
            if left not in self.grammar:
                self.grammar[left] = []
            productions = [p.strip() for p in right.split('|')]
            for prod in productions:
                if prod:
                    self.grammar[left].append(prod)
        if not self.grammar:
            raise ValueError("Invalid grammar format")
        self.original_start = list(self.grammar.keys())[0]
        self.start_symbol = self.original_start
        self.non_terminals = set(self.grammar.keys())
        self._identify_symbols()
        return self.grammar

    def _identify_symbols(self):
        self.terminals = set(['$'])
        all_symbols = set()
        for productions in self.grammar.values():
            for prod in productions:
                if not prod or prod == 'ε':
                    continue
                symbols = self._split_production(prod)
                all_symbols.update(symbols)
        for symbol in all_symbols:
            if symbol in self.non_terminals:
                continue
            if symbol == 'ε':
                self.terminals.add(symbol)
            elif symbol.isupper() and len(symbol) == 1:
                self.non_terminals.add(symbol)
            else:
                self.terminals.add(symbol)
        for term in ['id', 'num', 'a', 'b', 'c', 'd', 'x', 'y', 'z']:
            if term in str(self.grammar):
                self.terminals.add(term)

    def _split_production(self, prod):
        if not prod or prod == 'ε':
            return []
        if ' ' in prod:
            return [token for token in prod.split() if token]
        potential_symbols = sorted(self.terminals.union(self.non_terminals), key=len, reverse=True)
        tokens = []
        i = 0
        while i < len(prod):
            if prod[i].isspace():
                i += 1
                continue
            matched = False
            for symbol in potential_symbols:
                if symbol and prod.startswith(symbol, i):
                    tokens.append(symbol)
                    i += len(symbol)
                    matched = True
                    break
            if not matched:
                tokens.append(prod[i])
                i += 1
        return tokens

    def augment_grammar(self):
        new_start = self.original_start + "'"
        self.augmented_grammar = OrderedDict()
        self.augmented_grammar[new_start] = [self.original_start]
        self.augmented_grammar.update(self.grammar)
        self.start_symbol = new_start
        self.non_terminals.add(new_start)
        self.productions = [(new_start, self.original_start)]
        for lhs, rhs_list in self.grammar.items():
            for rhs in rhs_list:
                self.productions.append((lhs, rhs))
        return self.augmented_grammar

    def compute_first_sets(self):
        self.first_sets = {t: {t} for t in self.terminals if t != 'ε'}
        for nt in self.non_terminals:
            self.first_sets[nt] = set()
        self.first_sets['ε'] = {'ε'}
        changed = True
        while changed:
            changed = False
            for lhs, rhs_list in self.augmented_grammar.items():
                for rhs in rhs_list:
                    if not rhs or rhs == 'ε':
                        if 'ε' not in self.first_sets[lhs]:
                            self.first_sets[lhs].add('ε')
                            changed = True
                        continue
                    symbols = self._split_production(rhs)
                    all_have_epsilon = True
                    for symbol in symbols:
                        if symbol in self.terminals:
                            if symbol != 'ε' and symbol not in self.first_sets[lhs]:
                                self.first_sets[lhs].add(symbol)
                                changed = True
                            all_have_epsilon = False
                            break
                        else:
                            first_of_symbol = self.first_sets.get(symbol, set())
                            to_add = first_of_symbol - {'ε'}
                            if not to_add.issubset(self.first_sets[lhs]):
                                self.first_sets[lhs].update(to_add)
                                changed = True
                            if 'ε' not in first_of_symbol:
                                all_have_epsilon = False
                                break
                    if all_have_epsilon and 'ε' not in self.first_sets[lhs]:
                        self.first_sets[lhs].add('ε')
                        changed = True
        return self.first_sets

    def compute_follow_sets(self):
        self.follow_sets = {nt: set() for nt in self.non_terminals}
        self.follow_sets[self.start_symbol].add('$')
        changed = True
        while changed:
            changed = False
            new_follow = {nt: set(self.follow_sets[nt]) for nt in self.non_terminals}
            for lhs, rhs_list in self.augmented_grammar.items():
                for rhs in rhs_list:
                    if not rhs or rhs == 'ε':
                        continue
                    symbols = self._split_production(rhs)
                    for i in range(len(symbols)):
                        B = symbols[i]
                        if B not in self.non_terminals:
                            continue
                        # Rule 2a
                        if i + 1 < len(symbols):
                            beta = symbols[i+1:]
                            first_beta = self._first_of_sequence(beta)
                            to_add = first_beta - {'ε'}
                            new_follow[B].update(to_add)
                            if 'ε' in first_beta and lhs != B:
                                new_follow[B].update(self.follow_sets[lhs])
                        else:
                            if lhs != B:
                                new_follow[B].update(self.follow_sets[lhs])
            for nt in self.non_terminals:
                if new_follow[nt] != self.follow_sets[nt]:
                    self.follow_sets[nt] = new_follow[nt]
                    changed = True
        return self.follow_sets

    def _first_of_sequence(self, symbols):
        if not symbols:
            return {'ε'}
        result = set()
        for symbol in symbols:
            if symbol in self.terminals:
                result.add(symbol)
                return result
            first_of_symbol = self.first_sets.get(symbol, set())
            if not first_of_symbol:
                return result
            result.update(first_of_symbol - {'ε'})
            if 'ε' not in first_of_symbol:
                return result
        result.add('ε')
        return result

    # --------------------- DFA Construction ---------------------
    def closure(self, items):
        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            current_items = list(closure_set)
            for item in current_items:
                lhs, rhs, dot_pos = item
                symbols = [] if not rhs or rhs == 'ε' else self._split_production(rhs)
                if dot_pos < len(symbols):
                    next_symbol = symbols[dot_pos]
                    if next_symbol in self.non_terminals:
                        for prod in self.augmented_grammar.get(next_symbol, []):
                            new_item = (next_symbol, prod, 0)
                            if new_item not in closure_set:
                                closure_set.add(new_item)
                                changed = True
        return frozenset(closure_set)

    def goto(self, items, symbol):
        goto_items = set()
        for item in items:
            lhs, rhs, dot_pos = item
            symbols = [] if not rhs or rhs == 'ε' else self._split_production(rhs)
            if dot_pos < len(symbols) and symbols[dot_pos] == symbol:
                goto_items.add((lhs, rhs, dot_pos + 1))
        return self.closure(goto_items) if goto_items else frozenset()

    def build_dfa(self):
        initial_item = (self.start_symbol, self.original_start, 0)
        I0 = self.closure([initial_item])
        self.states = [I0]
        self.dfa_transitions = {}
        queue = [I0]
        while queue:
            current_state = queue.pop(0)
            current_idx = self.states.index(current_state)
            symbols_after_dot = set()
            for item in current_state:
                lhs, rhs, dot_pos = item
                symbols = [] if not rhs or rhs == 'ε' else self._split_production(rhs)
                if dot_pos < len(symbols):
                    symbols_after_dot.add(symbols[dot_pos])
            for symbol in symbols_after_dot:
                goto_state = self.goto(current_state, symbol)
                if goto_state and len(goto_state) > 0:
                    if goto_state not in self.states:
                        self.states.append(goto_state)
                        queue.append(goto_state)
                    goto_idx = self.states.index(goto_state)
                    self.dfa_transitions[(current_idx, symbol)] = goto_idx
        return self.states, self.dfa_transitions

    # --------------------- Parsing Table ---------------------
    def build_parsing_table(self):
        self.parsing_table = {'ACTION': {}, 'GOTO': {}}
        self.conflicts = []
        for i in range(len(self.states)):
            self.parsing_table['ACTION'][i] = {}
            self.parsing_table['GOTO'][i] = {}
        # SHIFT
        for (state_idx, symbol), next_state_idx in self.dfa_transitions.items():
            if symbol in self.terminals and symbol != '$':
                action = f's{next_state_idx}'
                if symbol in self.parsing_table['ACTION'][state_idx]:
                    existing = self.parsing_table['ACTION'][state_idx][symbol]
                    if existing.startswith('r'):
                        self.conflicts.append(f"Shift-Reduce conflict in State I{state_idx}, symbol '{symbol}'")
                self.parsing_table['ACTION'][state_idx][symbol] = action
        # REDUCE
        for state_idx, state in enumerate(self.states):
            for item in state:
                lhs, rhs, dot_pos = item
                symbols = [] if not rhs else self._split_production(rhs)
                if dot_pos == len(symbols):
                    prod_num = next((i for i, (l, r) in enumerate(self.productions) if l == lhs and r == rhs), None)
                    if prod_num is None:
                        continue
                    if lhs == self.start_symbol and rhs == self.original_start:
                        self.parsing_table['ACTION'][state_idx]['$'] = 'acc'
                    else:
                        for terminal in self.follow_sets.get(lhs, set()):
                            if terminal == 'ε':
                                continue
                            action = f'r{prod_num}'
                            existing = self.parsing_table['ACTION'][state_idx].get(terminal)
                            if existing:
                                self.conflicts.append(f"Conflict in State I{state_idx}, symbol '{terminal}'")
                                continue
                            self.parsing_table['ACTION'][state_idx][terminal] = action
        # GOTO
        for (state_idx, symbol), next_state_idx in self.dfa_transitions.items():
            if symbol in self.non_terminals and symbol != self.start_symbol:
                self.parsing_table['GOTO'][state_idx][symbol] = next_state_idx
        return self.parsing_table, self.conflicts

    def parse_string(self, input_string):
        """Parse input string using SLR parsing table"""
        # If there are conflicts, we cannot parse with SLR(1)
        if self.conflicts:
            return {
                'success': False, 
                'steps': [], 
                'message': f'Cannot parse: Grammar has conflicts (not SLR(1)). Conflicts: {len(self.conflicts)} found.'
            }
        
        stack = [0]
        tokens = input_string.split() + ['$']
        input_ptr = 0
        
        steps = []
        step_num = 1
        
        while True:
            current_state = stack[-1]
            current_token = tokens[input_ptr]
            
            action = self.parsing_table['ACTION'].get(current_state, {}).get(current_token, 'error')
            
            stack_str = ' '.join([str(x) for x in stack])
            input_str = ' '.join(tokens[input_ptr:])
            
            if action == 'error':
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': 'ERROR'
                })
                return {'success': False, 'steps': steps, 'message': 'String not accepted'}
            
            if action == 'acc':
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': 'ACCEPT'
                })
                return {'success': True, 'steps': steps, 'message': 'String accepted'}
            
            if action.startswith('s'):
                next_state = int(action[1:])
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': f'Shift to I{next_state}'
                })
                
                stack.append(current_token)
                stack.append(next_state)
                input_ptr += 1
            
            elif action.startswith('r'):
                prod_num = int(action[1:])
                lhs, rhs = self.productions[prod_num]
                
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': f'Reduce by {lhs} -> {rhs if rhs else "ε"}'
                })
                
                if not rhs:
                    rhs_symbols = []
                else:
                    rhs_symbols = self._split_production(rhs)
                
                for _ in range(len(rhs_symbols) * 2):
                    stack.pop()
                
                state_after_pop = stack[-1]
                goto_state = self.parsing_table['GOTO'].get(state_after_pop, {}).get(lhs)
                
                if goto_state is None:
                    return {'success': False, 'steps': steps, 'message': 'GOTO error'}
                
                stack.append(lhs)
                stack.append(goto_state)
            
            step_num += 1
            
            if step_num > 1000:
                return {'success': False, 'steps': steps, 'message': 'Max steps exceeded'}

    def generate_dfa_diagram(self):
        return generate_dfa_diagram_image(self.states, self.dfa_transitions, self._split_production)

    # ====================== PDF GENERATION METHODS ======================
    
    def generate_comprehensive_pdf(self, input_string=None, parsing_result=None):
        """
        Generate a comprehensive PDF report with all parser data
        
        Args:
            input_string: Optional input string that was parsed
            parsing_result: Optional parsing result from parse_string()
        
        Returns:
            Path to the generated PDF file
        """
        try:
            # Import the comprehensive PDF generator
            from utils.pdf import generate_comprehensive_slr_pdf
            
            # Format states for PDF
            formatted_states = []
            for i, state in enumerate(self.states):
                items = []
                for item in state:
                    lhs, rhs, dot_pos = item
                    rhs_str = rhs if rhs else 'ε'
                    symbols = self._split_production(rhs_str)
                    # Create item string with dot
                    item_str = f"{lhs} → " + ' '.join(symbols[:dot_pos]) + ' • ' + ' '.join(symbols[dot_pos:])
                    items.append(item_str.strip())
                formatted_states.append({
                    'name': f'I{i}',
                    'is_start': i == 0,
                    'items': items
                })
            
            # Format transitions for PDF
            formatted_transitions = []
            for (state_idx, symbol), next_state_idx in self.dfa_transitions.items():
                formatted_transitions.append({
                    'from': f'I{state_idx}',
                    'symbol': symbol,
                    'to': f'I{next_state_idx}'
                })
            
            # Format parsing table for PDF
            parsing_table_formatted = {'ACTION': {}, 'GOTO': {}}
            if hasattr(self, 'parsing_table'):
                for state, actions in self.parsing_table.get('ACTION', {}).items():
                    parsing_table_formatted['ACTION'][str(state)] = actions
                for state, gotos in self.parsing_table.get('GOTO', {}).items():
                    parsing_table_formatted['GOTO'][str(state)] = gotos
            
            # Filter FIRST/FOLLOW sets to only include non-terminals
            first_sets_filtered = {nt: self.first_sets[nt] for nt in self.non_terminals if nt in self.first_sets}
            follow_sets_filtered = {nt: self.follow_sets[nt] for nt in self.non_terminals if nt in self.follow_sets}
            
            # Generate DFA diagram base64
            dfa_diagram = None
            try:
                dfa_diagram = self.generate_dfa_diagram()
            except Exception as diagram_error:
                print(f"Warning: Could not generate diagram for PDF: {diagram_error}")

            # Prepare parser data
            parser_data = {
                'grammar': self.grammar,
                'augmented_grammar': self.augmented_grammar,
                'productions': self.productions,
                'first_sets': first_sets_filtered,
                'follow_sets': follow_sets_filtered,
                'states': formatted_states,
                'transitions': formatted_transitions,
                'parsing_table': parsing_table_formatted,
                'conflicts': self.conflicts if hasattr(self, 'conflicts') else [],
                'is_slr1': len(self.conflicts) == 0 if hasattr(self, 'conflicts') else True,
                'start_symbol': self.start_symbol,
                'dfa_diagram': dfa_diagram,
                'terminals': sorted(list(self.terminals - {'$'})),
                'non_terminals': sorted(list(self.non_terminals))
            }
            
            # Add parsing result if available
            if input_string and parsing_result:
                parser_data['input_string'] = input_string
                parser_data['parsing_result'] = parsing_result
            
            # Generate PDF
            pdf_path = generate_comprehensive_slr_pdf(parser_data)
            
            return pdf_path
            
        except Exception as e:
            print(f"Error generating comprehensive PDF: {e}")
            import traceback
            traceback.print_exc()
            # Raise to let gen_pdf handle the fallback
            raise e

    def gen_pdf(self, input_string=None, parsing_result=None):
        """Generate PDF report (comprehensive if possible, simple as fallback)"""
        try:
            # Try comprehensive PDF first
            # Check if we have all necessary data
            if (hasattr(self, 'states') and hasattr(self, 'dfa_transitions') and 
                hasattr(self, 'parsing_table')):
                return self.generate_comprehensive_pdf(input_string, parsing_result)
            else:
                # Fallback to simple PDF
                from utils.pdf import generate_pdf
                return generate_pdf(self.grammar, self.start_symbol, self.first_sets, self.follow_sets)
        except Exception as e:
            print(f"Error in gen_pdf: {e}")
            # Ultimate fallback
            from utils.pdf import generate_pdf
            return generate_pdf(self.grammar, self.start_symbol, self.first_sets, self.follow_sets)

    def generate_pdf_preview(self, input_string=None, parsing_result=None):
        """Generate a preview of the PDF report (returns base64)"""
        try:
            # Generate the PDF first with all parameters
            pdf_path = self.gen_pdf(input_string, parsing_result)
            
            # Read PDF and convert to base64
            import base64
            with open(pdf_path, 'rb') as f:
                pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                'success': True,
                'pdf_base64': pdf_base64,
                'message': 'PDF preview generated'
            }
            
        except Exception as e:
            print(f"Error generating PDF preview: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate PDF preview'
            }