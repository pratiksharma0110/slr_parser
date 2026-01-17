from flask import request, jsonify, send_file
import traceback
from services.slr_service import SLRParser

def handle_parse_grammar():
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        parser = SLRParser()
        grammar = parser.parse_grammar(grammar_text)
        return jsonify({
            'success': True,
            'grammar': {k: v for k, v in grammar.items()},
            'terminals': sorted(list(parser.terminals - {'$'})),
            'non_terminals': sorted(list(parser.non_terminals))
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def handle_augment_grammar():
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        
        augmented_raw = parser.augment_grammar()
        
        augmented_with_dots = {}
        for lhs, rhs_list in augmented_raw.items():
            dotted_rhss = []
            for rhs in rhs_list:
                rhs_str = " ".join(rhs) if isinstance(rhs, list) else rhs
                dotted_rhss.append(f"· {rhs_str}".strip())
            augmented_with_dots[lhs] = dotted_rhss

        productions = []
        for i, (lhs, rhs) in enumerate(parser.productions):
            rhs_str = " ".join(rhs) if isinstance(rhs, list) else rhs
            dot_rhs = f"· {rhs_str}".strip() if rhs_str else "·"
            productions.append({
                'index': i, 
                'lhs': lhs, 
                'rhs': dot_rhs
            })

        return jsonify({
            'success': True,
            'augmented_grammar': augmented_with_dots,
            'productions': productions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def handle_compute_first_follow():
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        first_sets = parser.compute_first_sets()
        follow_sets = parser.compute_follow_sets()

        # Format for display
        first_formatted = {nt: sorted([x for x in first_sets[nt] if x in parser.terminals or x == 'ε'])
                           for nt in sorted(parser.non_terminals)}
        follow_formatted = {nt: sorted(list(follow_sets[nt])) for nt in sorted(parser.non_terminals)}

        return jsonify({
            'success': True,
            'first_sets': first_formatted,
            'follow_sets': follow_formatted
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def handle_build_dfa():
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        parser.compute_first_sets()
        parser.compute_follow_sets()
        states, transitions = parser.build_dfa()

        states_formatted = []
        for i, state in enumerate(states):
            items = []
            for lhs, rhs, dot_pos in state:
                symbols = parser._split_production(rhs) if rhs else []
                item_str = f"{lhs} -> "
                for j in range(len(symbols)):
                    if j == dot_pos:
                        item_str += ". "
                    item_str += symbols[j] + " "
                if dot_pos == len(symbols):
                    item_str += "."
                items.append(item_str.strip())
            states_formatted.append({'id': i, 'name': f'I{i}', 'items': items, 'is_start': i == 0})

        transitions_formatted = [{'from': f'I{from_state}', 'to': f'I{to_state}', 'symbol': symbol}
                                 for (from_state, symbol), to_state in transitions.items()]

        return jsonify({
            'success': True,
            'states': states_formatted,
            'transitions': transitions_formatted,
            'num_states': len(states)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def handle_generate_dfa_diagram():
    try:
        data = request.get_json(force=True) 
        print("Received data:", data)

        grammar_text = data.get('grammar', '')
        if not grammar_text:
            print("Error: No grammar provided")
            return jsonify({'success': False, 'error': 'No grammar provided'}), 400

        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        parser.compute_first_sets()
        parser.compute_follow_sets()
        parser.build_dfa()

        print(f"States: {len(parser.states)}, Transitions: {len(parser.dfa_transitions)}")

        diagram_base64 = parser.generate_dfa_diagram()
        print("DFA diagram generated successfully")

        return jsonify({'success': True, 'diagram': diagram_base64})

    except Exception as e:
        print("Exception in /api/generate-dfa-diagram:\n", traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 400


def handle_build_parsing_table():
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        parser.compute_first_sets()
        parser.compute_follow_sets()
        parser.build_dfa()
        parsing_table, conflicts = parser.build_parsing_table()

        all_terminals = sorted([t for t in parser.terminals if t != '$' and t != 'ε'])
        all_non_terminals = sorted([nt for nt in parser.non_terminals if nt != parser.start_symbol])

        table_rows = []
        for state in range(len(parser.states)):
            row = {'state': f'I{state}'}
            for terminal in all_terminals:
                row[terminal] = parsing_table['ACTION'].get(state, {}).get(terminal, '')
            row['$'] = parsing_table['ACTION'].get(state, {}).get('$', '')
            for non_terminal in all_non_terminals:
                row[non_terminal] = parsing_table['GOTO'].get(state, {}).get(non_terminal, '')
            table_rows.append(row)

        is_slr1 = len(conflicts) == 0
        return jsonify({
            'success': True,
            'parsing_table': {'rows': table_rows, 'action_columns': all_terminals + ['$'], 'goto_columns': all_non_terminals},
            'conflicts': conflicts,
            'has_conflicts': len(conflicts) > 0,
            'is_slr1': is_slr1,
            'message': 'Grammar is SLR(1)' if is_slr1 else f'Grammar is NOT SLR(1) - {len(conflicts)} conflicts found'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def handle_parse_string():
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        input_string = data.get('input_string', '')
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        parser.compute_first_sets()
        parser.compute_follow_sets()
        parser.build_dfa()
        parser.build_parsing_table()
        result = parser.parse_string(input_string)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def handle_verify_grammar():
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        tokenized_productions = {lhs: [parser._split_production(rhs) if rhs else [] for rhs in rhs_list]
                                 for lhs, rhs_list in parser.grammar.items()}
        return jsonify({
            'success': True,
            'grammar': grammar_text,
            'non_terminals': sorted(list(parser.non_terminals)),
            'terminals': sorted(list(parser.terminals - {'$'})),
            'tokenized_productions': tokenized_productions,
            'productions': [{'index': i, 'lhs': lhs, 'rhs': rhs if rhs else 'ε'}
                            for i, (lhs, rhs) in enumerate(parser.productions)]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
def handle_generate_pdf_notes():
    try:
        data = request.get_json(force=True)
        print("Received data:", data)

        grammar_text = data.get('grammar', '')
        input_string = data.get('input_string', '')
        
        if not grammar_text:
            print("Error: No grammar provided")
            return jsonify({'success': False, 'error': 'No grammar provided'}), 400

        # Create parser and compute everything
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        parser.compute_first_sets()
        parser.compute_follow_sets()
        
        # Build DFA and parsing table
        try:
            parser.build_dfa()
            parser.build_parsing_table()
        except Exception as dfa_error:
            print(f"Warning: Could not build full parser: {dfa_error}")
            # Continue with basic data
        
        # Try to parse the input string if provided
        parsing_result = None
        if input_string:
            try:
                parsing_result = parser.parse_string(input_string)
            except Exception as parse_error:
                print(f"Warning: Could not parse string: {parse_error}")
                # Continue without parsing results
        
        # Generate PDF using the new method
        pdf_path = parser.gen_pdf(input_string, parsing_result)
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name="SLR_Parser_Complete_Report.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print("Exception in /api/export-pdf:\n", traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 400

# Add a new handler for PDF preview
def handle_generate_pdf_preview():
    try:
        data = request.get_json(force=True)
        print("Received preview data:", data)

        grammar_text = data.get('grammar', '')
        input_string = data.get('input_string', '')
        
        if not grammar_text:
            return jsonify({'success': False, 'error': 'No grammar provided'}), 400

        # Create parser and compute everything
        parser = SLRParser()
        parser.parse_grammar(grammar_text)
        parser.augment_grammar()
        parser.compute_first_sets()
        parser.compute_follow_sets()
        
        # Build DFA and parsing table
        try:
            parser.build_dfa()
            parser.build_parsing_table()
        except:
            pass  # Continue with what we have
        
        # Try to parse the input string if provided
        parsing_result = None
        if input_string:
            try:
                parsing_result = parser.parse_string(input_string)
            except:
                pass
        
        # Generate PDF preview with parsing results if available
        result = parser.generate_pdf_preview(input_string, parsing_result)
        
        if result['success']:
            return jsonify({
                'success': True,
                'pdf_base64': result['pdf_base64'],
                'message': 'PDF preview generated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 400
        
    except Exception as e:
        print("Exception in /api/generate-pdf-preview:\n", traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 400
