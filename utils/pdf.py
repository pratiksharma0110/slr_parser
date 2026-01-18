from flask import Blueprint, request, send_file, jsonify
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
import base64
import tempfile
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import uuid
import json
from datetime import datetime

# Blueprint for PDF routes
pdf_bp = Blueprint('pdf', __name__)

def create_styles():
    styles = getSampleStyleSheet()
    
    def add_or_get_style(name, parent_name, **kwargs):
        if name in styles:
            return styles[name]
        
        new_style = ParagraphStyle(name=name, parent=styles[parent_name], **kwargs)
        styles.add(new_style)
        return new_style

    # Title style
    add_or_get_style(
        'CustomTitle',
        'Title',
        fontSize=24,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Main heading style
    add_or_get_style(
        'MainHeading',
        'Heading1',
        fontSize=16,
        textColor=colors.HexColor('#4A5568'),
        spaceBefore=25,
        spaceAfter=15,
        leftIndent=0
    )
    
    # Subheading style
    add_or_get_style(
        'SubHeading',
        'Heading2',
        fontSize=14,
        textColor=colors.black,
        spaceBefore=15,
        spaceAfter=10,
        leftIndent=0
    )
    
    add_or_get_style(
        'CustomCode',
        'Code',
        fontSize=10,
        fontName='Courier',
        textColor=colors.black,
        leftIndent=0,
        spaceAfter=4,
        spaceBefore=4,
        leading=12
    )
    
    # Normal style with better spacing
    add_or_get_style(
        'NormalSpaced',
        'Normal',
        fontSize=11,
        spaceAfter=12,
        spaceBefore=6,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    # Success style
    add_or_get_style(
        'Success',
        'Normal',
        fontSize=11,
        textColor=colors.HexColor('#276749'),
        backColor=colors.HexColor('#C6F6D5'),
        spaceAfter=12,
        spaceBefore=6,
        leading=14
    )
    
    # Error style
    add_or_get_style(
        'Error',
        'Normal',
        fontSize=11,
        textColor=colors.HexColor('#9B2C2C'),
        backColor=colors.HexColor('#FED7D7'),
        spaceAfter=12,
        spaceBefore=6,
        leading=14
    )
    
    return styles

# Main PDF document generator
def generate_comprehensive_slr_pdf(parser_data):
    file_name = f"slr_parser_report_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(tempfile.gettempdir(), file_name)
    
    doc = SimpleDocTemplate(
        file_path, 
        pagesize=letter,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    
    styles = create_styles()
    story = []
    
    story.append(Paragraph("<b>Theoretical Background & Definitions</b>", styles['MainHeading']))
    
    def add_definition_box(title, content):
        title_para = Paragraph(f"<b>{title}</b>", styles['Normal'])
        content_para = Paragraph(content.replace('\n', '<br/>'), styles['Normal'])
        def_data = [[title_para, content_para]]
        def_table = Table(def_data, colWidths=[2.2*inch, 4.8*inch])
        def_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        story.append(def_table)
        story.append(Spacer(1, 8))
    
    add_definition_box(
        "Context-Free Grammar (CFG)",
        "A formal grammar where each production rule is of the form A → α, \n where A is a single non-terminal symbol and \n α is a string of terminals and/or non-terminals. \nCFGs are used to define the syntax of programming languages."
    )
    
    add_definition_box(
        "SLR(1) Parser",
        "Simple LR(1) parser is a bottom-up parsing technique that uses LR(0) \n items and FOLLOW sets to construct parsing tables. \n SLR(1) parsers are less powerful than LR(1) parsers but more efficient to \n implement. The '1' indicates one symbol of lookahead."
    )
    
    add_definition_box(
        "FIRST Set",
        "FIRST(α) is the set of terminals that begin strings derived from α. \n If α can derive ε (empty string), then ε is also in FIRST(α). \nUsed to predict which production to use in top-down parsing."
    )
    
    add_definition_box(
        "FOLLOW Set",
        "FOLLOW(A) is the set of terminals that can appear immediately to the \n right of non-terminal A in some sentential form. Used in SLR \n parsing to determine when to reduce a production."
    )
    
    add_definition_box(
        "Canonical Collection of LR(0) Items",
        "The set of all possible LR(0) items (productions with a dot position) \n that can be reached from the augmented grammar. Each item \n represents a state in the parsing process, showing how much of a \n production has been recognized."
    )
    
    add_definition_box(
        "Augmented Grammar",
        "The original grammar with a new start symbol S' and production S' → S added. \n This ensures the parser has a unique accepting \n state and  simplifies parsing table construction."
    )
    
    story.append(PageBreak())
    
    story.append(Paragraph("<b>Step 1: Grammar Input & Verification</b>", styles['MainHeading']))
    
    story.append(Spacer(1, 10))
    
    synth_data = [
        ["Non-Terminals", Paragraph(", ".join(parser_data.get('non_terminals', [])), styles['Normal'])],
        ["Terminals", Paragraph(", ".join(parser_data.get('terminals', [])), styles['Normal'])],
        ["Start Symbol", parser_data.get('start_symbol', 'N/A')]
    ]
    synth_table = Table(synth_data, colWidths=[2*inch, 4*inch])
    synth_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (1, 0), (1, -1), 12),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    
    # Group subheading and table to stay on the same page
    story.append(KeepTogether([
        Paragraph("<b>Grammar Synthesis:</b>", styles['SubHeading']),
        synth_table,
        Spacer(1, 10)
    ]))

    story.append(Paragraph("<b>Original Grammar Rules:</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Production Rules Format:</i> A → α where A is a non-terminal and α is a string of terminals and/or non-terminals", styles['NormalSpaced']))
    story.append(Paragraph("<i>ε (epsilon) represents the empty string.</i>", styles['NormalSpaced']))
    story.append(Spacer(1, 8))
    
    if 'grammar' in parser_data:
        grammar = parser_data['grammar']
        prod_count = 1
        for nt, productions in grammar.items():
            story.append(Paragraph(f"<b>Non-Terminal: {nt}</b>", styles['SubHeading']))
            for prod in productions:
                prod_display = prod if prod else "ε"
                story.append(Paragraph(f"{prod_count}. {nt} → {prod_display}", styles['CustomCode']))
                if prod == "ε":
                    story.append(Paragraph("   <i>→ Derives empty string</i>", styles['NormalSpaced']))
                else:
                    symbols = prod.split()
                    term_count = len([s for s in symbols if not s.isupper() or len(s) > 1])
                    nonterm_count = len([s for s in symbols if s.isupper() and len(s) == 1])
                    if term_count > 0 or nonterm_count > 0:
                        story.append(Paragraph(f"   <i>→ Contains {term_count} terminal(s) and {nonterm_count} non-terminal(s)</i>", styles['NormalSpaced']))
                prod_count += 1
            story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>Step 2: Augmented Grammar</b>", styles['MainHeading']))
    
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>Augmented Grammar Rules:</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Note:</i> S' → S is added as production 0 (numbering starts from 0)", styles['NormalSpaced']))
    story.append(Spacer(1, 8))
    
    if 'augmented_grammar' in parser_data:
        aug_grammar = parser_data['augmented_grammar']
        for nt, productions in aug_grammar.items():
            for prod in productions:
                story.append(Paragraph(f"<b>{nt}</b> → {prod}", styles['CustomCode']))
    
    story.append(Spacer(1, 10))
    # Group numbered productions
    if 'productions' in parser_data:
        productions = parser_data['productions']
        table_data = [["ID", "Production Rule"]]
        for i, (lhs, rhs) in enumerate(productions):
            rhs_str = rhs if rhs else "ε"
            table_data.append([str(i), Paragraph(f"{lhs} → {rhs_str}", styles['CustomCode'])])
        
        table = Table(table_data, colWidths=[0.8*inch, 4.2*inch])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (1, 0), (1, -1), 12)
        ]))
        
        story.append(KeepTogether([
            Paragraph("<b>Numbered Productions (Canonical Order):</b>", styles['SubHeading']),
            table,
            Spacer(1, 10)
        ]))
    
    # Group FIRST/FOLLOW subheading and table
    if 'first_sets' in parser_data and 'follow_sets' in parser_data:
        set_data = [["Non-Terminal", "FIRST Set", "FOLLOW Set"]]
        all_nts = sorted(parser_data['first_sets'].keys())
        for nt in all_nts:
            first_set = parser_data['first_sets'].get(nt, [])
            follow_set = parser_data['follow_sets'].get(nt, [])
            set_data.append([
                nt, 
                Paragraph(", ".join(sorted(first_set)), styles['Normal']),
                Paragraph(", ".join(sorted(follow_set)), styles['Normal'])
            ])
        
        set_table = Table(set_data, colWidths=[1.3*inch, 2.2*inch, 2.2*inch])
        set_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (1, 0), (2, -1), 8)
        ]))
        
        story.append(KeepTogether([
            Paragraph("<b>Step 3: FIRST & FOLLOW Sets</b>", styles['MainHeading']),
            set_table,
            Spacer(1, 10)
        ]))
    
    
    # Group Step 4 intro
    story.append(KeepTogether([
        Paragraph("<b>Step 4: DFA Builder - Canonical Collection of LR(0) Items</b>", styles['MainHeading']),
        Paragraph("<b>LR(0) Items:</b>", styles['SubHeading']),
        Paragraph("An LR(0) item is a production A → α•β where:", styles['NormalSpaced']),
        Paragraph("• α: symbols already recognized (left of dot)", styles['CustomCode']),
        Paragraph("• β: symbols yet to be recognized (right of dot)", styles['CustomCode']),
        Paragraph("• •: current position in the production", styles['CustomCode']),
        Paragraph("<i>Example:</i> E → E • + T means we have recognized E and expect + T", styles['NormalSpaced']),
        Spacer(1, 10)
    ]))
    
    if parser_data.get('dfa_diagram'):
        story.append(Paragraph("<b>4.1 DFA Canonical Collection Visual:</b>", styles['SubHeading']))
        try:
            img_data = base64.b64decode(parser_data['dfa_diagram'])
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                tmp_img.write(img_data)
                tmp_img_path = tmp_img.name
            story.append(Image(tmp_img_path, width=6.5*inch, height=4.5*inch, kind='proportional'))
            story.append(Spacer(1, 0.1*inch))
        except:
            pass

    dfa_states_elements = [Paragraph("<b>4.2 LR(0) Item Sets (States):</b>", styles['SubHeading'])]
    if 'states' in parser_data:
        states = parser_data['states']
        state_chunks = [states[i:i+2] for i in range(0, len(states), 2)]
        for chunk in state_chunks:
            row_cells = []
            for state in chunk:
                state_html = f"<b>State {state['name']}{' (Start)' if state.get('is_start') else ''}:</b><br/>"
                for item in state.get('items', []):
                    # Production rules start directly from the left
                    state_html += f"{item}<br/>"
                row_cells.append(Paragraph(state_html, styles['CustomCode']))
            
            if len(row_cells) < 2: 
                row_cells.append(Paragraph("", styles['Normal']))
            
            state_table = Table([row_cells], colWidths=[3.25*inch, 3.25*inch])
            state_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 10),
            ]))
            dfa_states_elements.append(KeepTogether([state_table, Spacer(1, 8)]))
    story.append(KeepTogether(dfa_states_elements))

    # Group Step 5 intro and conflict info
    story.append(KeepTogether([
        Paragraph("<b>Step 5: SLR Parsing Table Construction</b>", styles['MainHeading']),
        Spacer(1, 8),
        Paragraph("<b>Conflict Types in SLR Parsing:</b>", styles['SubHeading']),
        Paragraph("<b>Shift-Reduce Conflict:</b> Both shift and reduce actions in same cell", styles['NormalSpaced']),
        Paragraph("<b>Reduce-Reduce Conflict:</b> Multiple reduce actions in same cell", styles['NormalSpaced']),
        Paragraph("<i>Note:</i> Grammar is SLR(1) if no conflicts exist", styles['NormalSpaced']),
        Spacer(1, 10)
    ]))
    
    story.append(Paragraph("<b>5.1 Complete SLR Parsing Table (ACTION & GOTO):</b>", styles['SubHeading']))
    
    if 'parsing_table' in parser_data:
        pt = parser_data['parsing_table']
        action_table = pt.get('ACTION', {})
        goto_table = pt.get('GOTO', {})
        
        terms = set()
        for s in action_table.values(): terms.update(s.keys())
        terms = sorted(list(terms))
        if '$' in terms: terms.remove('$'); terms.append('$')
            
        nonterms = set()
        for s in goto_table.values(): nonterms.update(s.keys())
        nonterms = sorted(list(nonterms))
        
        # Custom header with spans for ACTION and GOTO - more robust construction
        header1 = ["State"]
        # ACTION header
        if len(terms) > 0:
            header1.append("ACTION")
            header1 += [""] * (len(terms) - 1)
        # GOTO header
        if len(nonterms) > 0:
            header1.append("GOTO")
            header1 += [""] * (len(nonterms) - 1)
        
        header2 = [""] + terms + nonterms
        full_table_data = [header1, header2]
        
        all_state_ids = sorted([int(k) for k in action_table.keys()])
        for sid in all_state_ids:
            sid_str = str(sid)
            row = [f"I{sid}"]
            row += [action_table.get(sid_str, {}).get(t, "") for t in terms]
            row += [goto_table.get(sid_str, {}).get(nt, "") for nt in nonterms]
            full_table_data.append(row)
            
        n_cols = len(terms) + len(nonterms) + 1
        available_width = 7.0 * inch
        col_w = available_width / n_cols
        
        # Adjust font size if many columns
        table_font_size = 8
        if n_cols > 15: table_font_size = 6
        elif n_cols > 10: table_font_size = 7
        
        parsing_table = Table(full_table_data, colWidths=[col_w] * n_cols)
        
        p_style = [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            # Vertical divider between ACTION and GOTO
            ('LINEAFTER', (len(terms), 0), (len(terms), -1), 1.5, colors.black),
            # Span headers
            ('SPAN', (1, 0), (len(terms), 0)), # ACTION span
            ('SPAN', (len(terms) + 1, 0), (n_cols - 1, 0)), # GOTO span
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), table_font_size),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 2)
        ]
        
        # Style row colors
        for r_idx, row in enumerate(full_table_data[2:], 2):
            for c_idx, cell in enumerate(row):
                if not cell: continue
                cell_str = str(cell) if isinstance(cell, int) else cell
                if cell_str.startswith('s'): p_style.append(('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.darkblue))
                elif cell_str.startswith('r'): p_style.append(('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.darkred))
                elif cell_str == 'acc': p_style.append(('BACKGROUND', (c_idx, r_idx), (c_idx, r_idx), colors.lightgreen))
        
        parsing_table.setStyle(TableStyle(p_style))
        story.append(parsing_table)
    else:
        story.append(Paragraph("<i>Parsing table not available. Please build the parsing table first.</i>", styles['NormalSpaced']))

    if parser_data.get('conflicts'):
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Warning: {len(parser_data['conflicts'])} conflicts found!</b>", styles['Error']))
        for conflict in parser_data['conflicts']:
            story.append(Paragraph(f"• {conflict}", styles['Error']))

    if 'parsing_result' in parser_data:
        res = parser_data['parsing_result']
        status_box = styles['Success'] if res.get('success') else styles['Error']
        
        if res.get('steps'):
            trace_data = [["Step", "Stack Content", "Input Buffer", "Action Taken"]]
            for s in res['steps']:
                trace_data.append([
                    str(s['step']), 
                    Paragraph(s['stack'], styles['CustomCode']), 
                    Paragraph(s['input'], styles['CustomCode']), 
                    Paragraph(s['action'], styles['Normal'])
                ])
            
            trace_table = Table(trace_data, colWidths=[0.5*inch, 2.5*inch, 1.2*inch, 2.3*inch])
            trace_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (-1, -1), 'LEFT'),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            
            story.append(KeepTogether([
                Paragraph("<b>Step 6: Input String Parsing Algorithm</b>", styles['MainHeading']),
                Paragraph(f"<b>Test Input:</b> {parser_data.get('input_string', 'Empty')}", styles['NormalSpaced']),
                Paragraph(f"<b>Parsing Result:</b> {res.get('message', 'N/A')}", status_box),
                trace_table
            ]))

    story.append(Spacer(1, 0.5*inch))
    
    doc.build(story)
    return file_path

# API route for PDF export
@pdf_bp.route('/export-pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.json
        from slr_service import SLRParser
        
        parser = SLRParser()
        grammar_text = data.get('grammar', '')
        
        if not grammar_text:
            return jsonify({'success': False, 'error': 'No grammar provided'})
        
        # Parse grammar
        grammar = parser.parse_grammar(grammar_text)
        
        # Augment grammar
        augmented_grammar = parser.augment_grammar()
        
        # Compute FIRST and FOLLOW
        first_sets = parser.compute_first_sets()
        follow_sets = parser.compute_follow_sets()
        
        # Build DFA
        states, transitions = parser.build_dfa()
        
        # Format states for PDF
        formatted_states = []
        for i, state in enumerate(states):
            items = []
            for item in state:
                lhs, rhs, dot_pos = item
                rhs_str = rhs if rhs else 'ε'
                symbols = parser._split_production(rhs_str)
                item_str = f"{lhs} → " + ' '.join(symbols[:dot_pos]) + ' • ' + ' '.join(symbols[dot_pos:])
                items.append(item_str)
            formatted_states.append({
                'name': f'I{i}',
                'is_start': i == 0,
                'items': items
            })
        
        # Format transitions for PDF
        formatted_transitions = []
        for (state_idx, symbol), next_state_idx in transitions.items():
            formatted_transitions.append({
                'from': f'I{state_idx}',
                'symbol': symbol,
                'to': f'I{next_state_idx}'
            })
        
        # Build parsing table
        parsing_table, conflicts = parser.build_parsing_table()
        
        # Check if grammar is SLR(1)
        is_slr1 = len(conflicts) == 0
        parser_data = {
            'grammar': grammar,
            'augmented_grammar': augmented_grammar,
            'productions': parser.productions,
            'first_sets': first_sets,
            'follow_sets': follow_sets,
            'states': formatted_states,
            'transitions': formatted_transitions,
            'parsing_table': parsing_table,
            'conflicts': conflicts,
            'is_slr1': is_slr1,
            'start_symbol': parser.start_symbol
        }
        
        pdf_path = generate_comprehensive_slr_pdf(parser_data)
        
        # Return PDF file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name='SLR_Parser_Report.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
def generate_pdf(grammar, start_symbol, first, follow):
    file_name = f"grammar_notes_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join("/tmp", file_name)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    story = []

    story.append(Paragraph("<b>Compiler Design Notes</b>", styles["Title"]))
    story.append(Paragraph(
        "Grammar, FIRST and FOLLOW (Auto-generated)",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>1. Input Grammar</b>", styles["Heading2"]))
    for nt, productions in grammar.items():
        for p in productions:
            story.append(Paragraph(f"{nt} → {p}", styles["Normal"]))

    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>2. Grammar Definition</b>", styles["Heading2"]))
    story.append(Paragraph("Type: Context-Free Grammar (CFG)", styles["Normal"]))
    story.append(Paragraph(f"Start Symbol: {start_symbol}", styles["Normal"]))

    non_terminals = ", ".join(grammar.keys())
    story.append(Paragraph(f"Non-terminals: {{ {non_terminals} }}", styles["Normal"]))

    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>3. FIRST Set</b>", styles["Heading2"]))
    story.append(Paragraph(
        "FIRST(X) is the set of terminals that begin strings derivable from X.",
        styles["Normal"]
    ))

    for nt, values in first.items():
        story.append(
            Paragraph(f"FIRST({nt}) = {{ {', '.join(values)} }}", styles["Normal"])
        )

    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>4. FOLLOW Set</b>", styles["Heading2"]))
    story.append(Paragraph(
        "FOLLOW(A) is the set of terminals that can appear immediately to the right of A.",
        styles["Normal"]
    ))

    for nt, values in follow.items():
        story.append(
            Paragraph(f"FOLLOW({nt}) = {{ {', '.join(values)} }}", styles["Normal"])
        )

    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>5. FIRST & FOLLOW Summary</b>", styles["Heading2"]))

    table_data = [["Non-Terminal", "FIRST", "FOLLOW"]]
    for nt in grammar.keys():
        table_data.append([
            nt,
            ", ".join(first.get(nt, [])),
            ", ".join(follow.get(nt, []))
        ])

    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)
    ]))

    story.append(table)

    story.append(Spacer(1, 12))

    doc.build(story)
    return file_path
