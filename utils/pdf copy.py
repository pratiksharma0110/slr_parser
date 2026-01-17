from flask import Blueprint, request, send_file, jsonify
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
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

# Create blueprint for PDF routes
pdf_bp = Blueprint('pdf', __name__)

def create_styles():
    """Create custom styles for the PDF"""
    styles = getSampleStyleSheet()
    
    # helper to add or update styles
    def add_or_get_style(name, parent_name, **kwargs):
        if name in styles:
            # Update existing style or just return it
            # For simplicity, we'll just use the existing one if it's there
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
        fontSize=18,
        textColor=colors.HexColor('#4A5568'),
        spaceBefore=20,
        spaceAfter=10,
        leftIndent=0
    )
    
    # Subheading style
    add_or_get_style(
        'SubHeading',
        'Heading2',
        fontSize=14,
        textColor=colors.HexColor('#2D3748'),
        spaceBefore=15,
        spaceAfter=8,
        backColor=colors.HexColor('#EDF2F7'),
        leftIndent=10
    )
    
    # Code style - Use a more unique name to avoid conflict with built-in 'Code'
    add_or_get_style(
        'CustomCode',
        'Code',
        fontSize=10,
        fontName='Courier',
        textColor=colors.HexColor('#2D3748'),
        backColor=colors.HexColor('#F7FAFC'),
        leftIndent=20,
        borderPadding=5,
        borderWidth=1,
        borderColor=colors.HexColor('#E2E8F0')
    )
    
    # Normal style with better spacing
    add_or_get_style(
        'NormalSpaced',
        'Normal',
        fontSize=11,
        spaceAfter=8,
        alignment=TA_JUSTIFY
    )
    
    # Success style
    add_or_get_style(
        'Success',
        'Normal',
        fontSize=11,
        textColor=colors.HexColor('#276749'),
        backColor=colors.HexColor('#C6F6D5'),
        spaceAfter=8
    )
    
    # Error style
    add_or_get_style(
        'Error',
        'Normal',
        fontSize=11,
        textColor=colors.HexColor('#9B2C2C'),
        backColor=colors.HexColor('#FED7D7'),
        spaceAfter=8
    )
    
    return styles

def generate_comprehensive_slr_pdf(parser_data):
    """
    Generate a comprehensive PDF with all SLR parsing steps.
    Enhanced for exam-type notes with complete definitions and detailed explanations.
    """
    # Generate unique filename
    file_name = f"slr_parser_report_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(tempfile.gettempdir(), file_name)
    
    # Create document
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
    
    # ---------- COVER PAGE ----------
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("<b>SLR PARSER DESIGN - COMPREHENSIVE STUDY NOTES</b>", styles['CustomTitle']))
    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph("<center>Complete Technical Analysis with Definitions, Algorithms, and Implementation Details</center>", styles['NormalSpaced']))
    story.append(Paragraph("<center>Ideal for Compiler Design Examination Preparation</center>", styles['NormalSpaced']))
    story.append(Spacer(1, 0.5*inch))
    
    # Create a summary box on cover
    summary_info = [
        ["Document Type", "Complete Study Material with Exam Notes"],
        ["Generated Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ["Grammar Status", "SLR(1) Compliant" if parser_data.get('is_slr1') else "Contains Conflicts"],
        ["Topics Covered", "Grammar Analysis, FIRST/FOLLOW, DFA, Parsing Table, String Parsing"]
    ]
    summary_table = Table(summary_info, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F7FAFC')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))
    
    # ---------- THEORETICAL BACKGROUND ----------
    story.append(Paragraph("<b>Theoretical Background & Definitions</b>", styles['MainHeading']))
    
    # Definition boxes
    def add_definition_box(title, content):
        def_data = [["<b>" + title + "</b>", content]]
        def_table = Table(def_data, colWidths=[1.8*inch, 4.2*inch])
        def_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4299E1')),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#EBF8FF')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#F7FAFC')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        story.append(def_table)
        story.append(Spacer(1, 8))
    
    add_definition_box(
        "Context-Free Grammar (CFG)",
        "A formal grammar where each production rule is of the form A → α, where A is a single non-terminal symbol and α is a string of terminals and/or non-terminals. CFGs are used to define the syntax of programming languages."
    )
    
    add_definition_box(
        "SLR(1) Parser",
        "Simple LR(1) parser is a bottom-up parsing technique that uses LR(0) items and FOLLOW sets to construct parsing tables. SLR(1) parsers are less powerful than LR(1) parsers but more efficient to implement. The '1' indicates one symbol of lookahead."
    )
    
    add_definition_box(
        "FIRST Set",
        "FIRST(α) is the set of terminals that begin strings derived from α. If α can derive ε (empty string), then ε is also in FIRST(α). Used to predict which production to use in top-down parsing."
    )
    
    add_definition_box(
        "FOLLOW Set",
        "FOLLOW(A) is the set of terminals that can appear immediately to the right of non-terminal A in some sentential form. Used in SLR parsing to determine when to reduce a production."
    )
    
    add_definition_box(
        "Canonical Collection of LR(0) Items",
        "The set of all possible LR(0) items (productions with a dot position) that can be reached from the augmented grammar. Each item represents a state in the parsing process, showing how much of a production has been recognized."
    )
    
    add_definition_box(
        "Augmented Grammar",
        "The original grammar with a new start symbol S' and production S' → S added. This ensures the parser has a unique accepting state and simplifies parsing table construction."
    )
    
    story.append(PageBreak())
    
    # ---------- STEP 1. GRAMMAR INPUT & VERIFICATION ----------
    story.append(Paragraph("<b>Step 1: Grammar Input & Verification</b>", styles['MainHeading']))
    
    # Add algorithm explanation
    story.append(Paragraph("<b>Algorithm 1: Grammar Analysis</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Input:</i> Context-Free Grammar G = (V, T, P, S)", styles['CustomCode']))
    story.append(Paragraph("<i>Output:</i> Verified grammar with identified terminals and non-terminals", styles['CustomCode']))
    story.append(Paragraph("<i>Steps:</i>", styles['NormalSpaced']))
    story.append(Paragraph("1. Parse each production rule A → α₁ | α₂ | ... | αₙ", styles['CustomCode']))
    story.append(Paragraph("2. Identify non-terminals V = {A₁, A₂, ..., Aₘ} (left side of productions)", styles['CustomCode']))
    story.append(Paragraph("3. Identify terminals T = all symbols not in V", styles['CustomCode']))
    story.append(Paragraph("4. Set start symbol S = first production's left side", styles['CustomCode']))
    story.append(Spacer(1, 10))
    
    # Grammar Synthesis Table
    story.append(Paragraph("<b>Grammar Synthesis:</b>", styles['SubHeading']))
    synth_data = [
        ["Non-Terminals", ", ".join(parser_data.get('non_terminals', []))],
        ["Terminals", ", ".join(parser_data.get('terminals', []))],
        ["Start Symbol", parser_data.get('start_symbol', 'N/A')]
    ]
    synth_table = Table(synth_data, colWidths=[1.5*inch, 4.5*inch])
    synth_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EDF2F7')),
    ]))
    story.append(synth_table)
    story.append(Spacer(1, 10))

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
                # Add explanation for each production
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
    
    # ---------- STEP 2. AUGMENTED GRAMMAR ----------
    story.append(Paragraph("<b>Step 2: Augmented Grammar</b>", styles['MainHeading']))
    
    # Add algorithm explanation
    story.append(Paragraph("<b>Algorithm 2: Grammar Augmentation</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Input:</i> Grammar G = (V, T, P, S) with start symbol S", styles['CustomCode']))
    story.append(Paragraph("<i>Output:</i> Augmented Grammar G' = (V ∪ {S'}, T, P ∪ {S' → S}, S')", styles['CustomCode']))
    story.append(Paragraph("<i>Purpose:</i> Ensure unique accepting state and simplify parsing", styles['NormalSpaced']))
    story.append(Paragraph("<i>Steps:</i>", styles['NormalSpaced']))
    story.append(Paragraph("1. Create new start symbol S' = S + '", styles['CustomCode']))
    story.append(Paragraph("2. Add production S' → S", styles['CustomCode']))
    story.append(Paragraph("3. Set S' as the new start symbol", styles['CustomCode']))
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
    story.append(Paragraph("<b>Numbered Productions (Canonical Order):</b>", styles['SubHeading']))
    if 'productions' in parser_data:
        productions = parser_data['productions']
        table_data = [["ID", "Production Rule"]]
        for i, (lhs, rhs) in enumerate(productions):
            rhs_str = rhs if rhs else "ε"
            table_data.append([str(i), f"{lhs} → {rhs_str}"])
        
        table = Table(table_data, colWidths=[0.6*inch, 4.4*inch])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CBD5E0')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(table)
    
    # ---------- STEP 3. FIRST & FOLLOW SETS ----------
    story.append(Paragraph("<b>Step 3: FIRST & FOLLOW Sets</b>", styles['MainHeading']))
    
    # FIRST Set Algorithm
    story.append(Paragraph("<b>Algorithm 3: Computing FIRST Sets</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Input:</i> Grammar G = (V, T, P, S)", styles['CustomCode']))
    story.append(Paragraph("<i>Output:</i> FIRST(A) for all A ∈ V ∪ T", styles['CustomCode']))
    story.append(Paragraph("<i>Rules:</i>", styles['NormalSpaced']))
    story.append(Paragraph("1. If X is terminal, FIRST(X) = {X}", styles['CustomCode']))
    story.append(Paragraph("2. If X → ε is production, add ε to FIRST(X)", styles['CustomCode']))
    story.append(Paragraph("3. If X → Y₁Y₂...Yₖ and ε ∈ FIRST(Yᵢ) for i=1 to j-1, add FIRST(Yⱼ) - {ε} to FIRST(X)", styles['CustomCode']))
    story.append(Paragraph("4. If ε ∈ FIRST(Yᵢ) for all i, add ε to FIRST(X)", styles['CustomCode']))
    story.append(Spacer(1, 8))
    
    # FOLLOW Set Algorithm
    story.append(Paragraph("<b>Algorithm 4: Computing FOLLOW Sets</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Input:</i> Grammar G with start symbol S and FIRST sets", styles['CustomCode']))
    story.append(Paragraph("<i>Output:</i> FOLLOW(A) for all A ∈ V", styles['CustomCode']))
    story.append(Paragraph("<i>Rules:</i>", styles['NormalSpaced']))
    story.append(Paragraph("1. Add $ to FOLLOW(S) where S is start symbol", styles['CustomCode']))
    story.append(Paragraph("2. For production A → αBβ, add FIRST(β) - {ε} to FOLLOW(B)", styles['CustomCode']))
    story.append(Paragraph("3. For production A → αB or A → αBβ where ε ∈ FIRST(β), add FOLLOW(A) to FOLLOW(B)", styles['CustomCode']))
    story.append(Spacer(1, 10))
    
    set_data = [["Non-Terminal", "FIRST Set", "FOLLOW Set"]]
    if 'first_sets' in parser_data and 'follow_sets' in parser_data:
        all_nts = sorted(parser_data['first_sets'].keys())
        for nt in all_nts:
            first_set = parser_data['first_sets'].get(nt, [])
            follow_set = parser_data['follow_sets'].get(nt, [])
            set_data.append([
                nt, 
                "{ " + ", ".join(sorted(first_set)) + " }",
                "{ " + ", ".join(sorted(follow_set)) + " }"
            ])
        
        set_table = Table(set_data, colWidths=[1.2*inch, 2.4*inch, 2.4*inch])
        set_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(set_table)
    
    story.append(PageBreak())
    
    # ---------- STEP 4. DFA BUILDER ----------
    story.append(Paragraph("<b>Step 4: DFA Builder - Canonical Collection of LR(0) Items</b>", styles['MainHeading']))
    
    # DFA Construction Algorithm
    story.append(Paragraph("<b>Algorithm 5: Building Canonical Collection</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Input:</i> Augmented Grammar G'", styles['CustomCode']))
    story.append(Paragraph("<i>Output:</i> Set of LR(0) items C = {I₀, I₁, ..., Iₙ}", styles['CustomCode']))
    story.append(Paragraph("<i>Key Functions:</i>", styles['NormalSpaced']))
    story.append(Paragraph("• CLOSURE(I): Set of items reachable from I using ε-productions", styles['CustomCode']))
    story.append(Paragraph("• GOTO(I, X): Set of items reachable from I on symbol X", styles['CustomCode']))
    story.append(Paragraph("<i>Algorithm:</i>", styles['NormalSpaced']))
    story.append(Paragraph("1. I₀ = CLOSURE({[S' → •S]})", styles['CustomCode']))
    story.append(Paragraph("2. C = {I₀}", styles['CustomCode']))
    story.append(Paragraph("3. For each I ∈ C and symbol X:", styles['CustomCode']))
    story.append(Paragraph("   a. If GOTO(I, X) is not empty and not in C:", styles['CustomCode']))
    story.append(Paragraph("      i. Add GOTO(I, X) to C", styles['CustomCode']))
    story.append(Paragraph("   b. Repeat until no new items can be added", styles['CustomCode']))
    story.append(Spacer(1, 8))
    
    # LR(0) Item Definition
    story.append(Paragraph("<b>LR(0) Items:</b>", styles['SubHeading']))
    story.append(Paragraph("An LR(0) item is a production A → α•β where:", styles['NormalSpaced']))
    story.append(Paragraph("• α: symbols already recognized (left of dot)", styles['CustomCode']))
    story.append(Paragraph("• β: symbols yet to be recognized (right of dot)", styles['CustomCode']))
    story.append(Paragraph("• •: current position in the production", styles['CustomCode']))
    story.append(Paragraph("<i>Example:</i> E → E • + T means we have recognized E and expect + T", styles['NormalSpaced']))
    story.append(Spacer(1, 10))
    
    # DFA Diagram
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

    # DFA States
    story.append(Paragraph("<b>4.2 LR(0) Item Sets (States):</b>", styles['SubHeading']))
    if 'states' in parser_data:
        states = parser_data['states']
        state_chunks = [states[i:i+2] for i in range(0, len(states), 2)]
        for chunk in state_chunks:
            row_cells = []
            for state in chunk:
                state_html = f"<b>State {state['name']}{' (Start)' if state.get('is_start') else ''}:</b><br/>"
                for item in state.get('items', []):
                    state_html += f"&nbsp;&nbsp;{item}<br/>"
                row_cells.append(Paragraph(state_html, styles['CustomCode']))
            if len(row_cells) < 2: row_cells.append(Paragraph("", styles['Normal']))
            story.append(Table([row_cells], colWidths=[3.2*inch, 3.2*inch], style=[('VALIGN', (0,0), (-1,-1), 'TOP')]))

    # ---------- STEP 5. SLR PARSING TABLE ----------
    story.append(Paragraph("<b>Step 5: SLR Parsing Table Construction</b>", styles['MainHeading']))
    
    # Parsing Table Algorithm
    story.append(Paragraph("<b>Algorithm 6: SLR Parsing Table Construction</b>", styles['SubHeading']))
    story.append(Paragraph("<i>Input:</i> Canonical Collection C = {I₀, I₁, ..., Iₙ} and FOLLOW sets", styles['CustomCode']))
    story.append(Paragraph("<i>Output:</i> Parsing Table with ACTION and GOTO entries", styles['CustomCode']))
    story.append(Paragraph("<i>Construction Rules:</i>", styles['NormalSpaced']))
    story.append(Paragraph("<b>ACTION Entries:</b>", styles['NormalSpaced']))
    story.append(Paragraph("1. If [A → α•aβ] ∈ Iᵢ and GOTO(Iᵢ, a) = Iⱼ, set ACTION[i,a] = shift j", styles['CustomCode']))
    story.append(Paragraph("2. If [A → α•] ∈ Iᵢ and A ≠ S', for each a ∈ FOLLOW(A), set ACTION[i,a] = reduce A→α", styles['CustomCode']))
    story.append(Paragraph("3. If [S' → S•] ∈ Iᵢ, set ACTION[i,$] = accept", styles['CustomCode']))
    story.append(Paragraph("<b>GOTO Entries:</b>", styles['NormalSpaced']))
    story.append(Paragraph("If GOTO(Iᵢ, A) = Iⱼ where A is non-terminal, set GOTO[i,A] = j", styles['CustomCode']))
    story.append(Spacer(1, 8))
    
    # Conflict Types
    story.append(Paragraph("<b>Conflict Types in SLR Parsing:</b>", styles['SubHeading']))
    story.append(Paragraph("<b>Shift-Reduce Conflict:</b> Both shift and reduce actions in same cell", styles['NormalSpaced']))
    story.append(Paragraph("<b>Reduce-Reduce Conflict:</b> Multiple reduce actions in same cell", styles['NormalSpaced']))
    story.append(Paragraph("<i>Note:</i> Grammar is SLR(1) if no conflicts exist", styles['NormalSpaced']))
    story.append(Spacer(1, 10))
    
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
        
        header1 = ["State"] + ["ACTION"] * len(terms) + ["GOTO"] * len(nonterms)
        header2 = [""] + terms + nonterms
        full_table_data = [header2]
        
        all_state_ids = sorted([int(k) for k in action_table.keys()])
        for sid in all_state_ids:
            sid_str = str(sid)
            row = [f"I{sid}"]
            row += [action_table.get(sid_str, {}).get(t, "") for t in terms]
            row += [goto_table.get(sid_str, {}).get(nt, "") for nt in nonterms]
            full_table_data.append(row)
            
        n_cols = len(terms) + len(nonterms) + 1
        col_w = 6.4 / n_cols
        parsing_table = Table(full_table_data, colWidths=[0.6*inch] + [col_w*inch] * (n_cols-1))
        
        p_style = [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1,-1), colors.white),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
        ]
        
        for r_idx, row in enumerate(full_table_data[1:], 1):
            for c_idx, cell in enumerate(row):
                if not cell: continue
                # Convert cell to string if it's an integer (for GOTO entries)
                cell_str = str(cell) if isinstance(cell, int) else cell
                if cell_str.startswith('s'): p_style.append(('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.darkblue))
                elif cell_str.startswith('r'): p_style.append(('TEXTCOLOR', (c_idx, r_idx), (c_idx, r_idx), colors.darkred))
                elif cell_str == 'acc': p_style.append(('BACKGROUND', (c_idx, r_idx), (c_idx, r_idx), colors.lightgreen))
        
        parsing_table.setStyle(TableStyle(p_style))
        story.append(parsing_table)

    # Conflict Analysis
    if parser_data.get('conflicts'):
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Warning: {len(parser_data['conflicts'])} conflicts found!</b>", styles['Error']))
        for conflict in parser_data['conflicts']:
            story.append(Paragraph(f"• {conflict}", styles['Error']))

    # ---------- STEP 6. INPUT STRING PARSER ----------
    if 'parsing_result' in parser_data:
        story.append(PageBreak())
        story.append(Paragraph("<b>Step 6: Input String Parsing Algorithm</b>", styles['MainHeading']))
        
        # String Parsing Algorithm
        story.append(Paragraph("<b>Algorithm 7: SLR String Parsing</b>", styles['SubHeading']))
        story.append(Paragraph("<i>Input:</i> Input string w and SLR parsing table", styles['CustomCode']))
        story.append(Paragraph("<i>Output:</i> Accept/Reject with parsing trace", styles['CustomCode']))
        story.append(Paragraph("<i>Data Structures:</i>", styles['NormalSpaced']))
        story.append(Paragraph("• Stack: Stores state symbols and input symbols", styles['CustomCode']))
        story.append(Paragraph("• Input Buffer: Remaining input to be processed", styles['CustomCode']))
        story.append(Paragraph("<i>Algorithm:</i>", styles['NormalSpaced']))
        story.append(Paragraph("1. Initialize: stack = [0], input = w$", styles['CustomCode']))
        story.append(Paragraph("2. Let a = next input symbol, s = top stack state", styles['CustomCode']))
        story.append(Paragraph("3. Consult ACTION[s,a]:", styles['CustomCode']))
        story.append(Paragraph("   a. If 'shift j': push a, then j; advance input", styles['CustomCode']))
        story.append(Paragraph("   b. If 'reduce A→β': pop 2|β| symbols, push A, then GOTO[new_top,A]", styles['CustomCode']))
        story.append(Paragraph("   c. If 'accept': string accepted", styles['CustomCode']))
        story.append(Paragraph("   d. If 'error': string rejected", styles['CustomCode']))
        story.append(Paragraph("4. Repeat from step 2", styles['CustomCode']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Test Input:</b> {parser_data.get('input_string', 'Empty')}", styles['NormalSpaced']))
        
        res = parser_data['parsing_result']
        status_box = styles['Success'] if res.get('success') else styles['Error']
        story.append(Paragraph(f"<b>Parsing Result:</b> {res.get('message', 'N/A')}", status_box))
        
        if res.get('steps'):
            trace_data = [["Step", "Stack Content", "Input Buffer", "Action Taken"]]
            for s in res['steps']:
                trace_data.append([str(s['step']), s['stack'], s['input'], s['action']])
            
            trace_table = Table(trace_data, colWidths=[0.5*inch, 2.3*inch, 1.4*inch, 2.3*inch])
            trace_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F7FAFC')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
            ]))
            story.append(trace_table)

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("<center><b>--- Technical Analysis Complete ---</b></center>", styles['NormalSpaced']))
    
    # ---------- EXAM PREPARATION SUMMARY ----------
    story.append(PageBreak())
    story.append(Paragraph("<b>Exam Preparation Summary</b>", styles['MainHeading']))
    
    # Key Points for Exam
    story.append(Paragraph("<b>Key Points for SLR(1) Parsing:</b>", styles['SubHeading']))
    key_points = [
        "SLR(1) uses LR(0) items + FOLLOW sets (simpler than LR(1))",
        "Augmented grammar ensures unique start state",
        "FIRST sets help predict productions in top-down parsing",
        "FOLLOW sets determine when to reduce in bottom-up parsing",
        "Canonical collection represents all possible parser states",
        "Parsing table conflicts indicate grammar is not SLR(1)",
        "Shift action: move dot over terminal, goto next state",
        "Reduce action: replace RHS with LHS using production rule"
    ]
    
    for i, point in enumerate(key_points, 1):
        story.append(Paragraph(f"{i}. {point}", styles['NormalSpaced']))
    
    story.append(Spacer(1, 12))
    
    # Common Exam Questions
    story.append(Paragraph("<b>Common Exam Questions:</b>", styles['SubHeading']))
    exam_questions = [
        "Q: Why do we augment the grammar?",
        "A: To ensure unique accepting state and simplify parser construction.",
        "",
        "Q: What is the difference between SLR(1) and LR(1)?",
        "A: SLR(1) uses FOLLOW sets, LR(1) uses lookahead sets - LR(1) is more powerful.",
        "",
        "Q: When do shift-reduce conflicts occur?",
        "A: When a state has both a shift item [A→α•aβ] and reduce item [B→γ•] with a∈FOLLOW(B).",
        "",
        "Q: What is the purpose of the CLOSURE function?",
        "A: To add all items reachable via ε-productions, ensuring completeness of parser states."
    ]
    
    for item in exam_questions:
        if item.startswith("Q:"):
            story.append(Paragraph(f"<b>{item}</b>", styles['NormalSpaced']))
        elif item.startswith("A:"):
            story.append(Paragraph(f"<i>{item}</i>", styles['NormalSpaced']))
        else:
            story.append(Paragraph(item, styles['NormalSpaced']))
    
    story.append(Spacer(1, 12))
    
    # Algorithm Complexity
    story.append(Paragraph("<b>Algorithm Complexity:</b>", styles['SubHeading']))
    complexity_info = [
        ["Algorithm", "Time Complexity", "Space Complexity"],
        ["FIRST/FOLLOW Computation", "O(n²)", "O(n²)"],
        ["Canonical Collection", "O(n³)", "O(n²)"],
        ["Parsing Table Construction", "O(n²)", "O(n²)"],
        ["String Parsing", "O(m)", "O(m)"],
        ["n = grammar size, m = input length", "", ""]
    ]
    
    complexity_table = Table(complexity_info, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    complexity_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(complexity_table)
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("<center><b>*** END OF STUDY MATERIALS ***</b></center>", styles['CustomTitle']))
    story.append(Paragraph("<center><i>Generated for Compiler Design Examination Preparation</i></center>", styles['NormalSpaced']))
    
    doc.build(story)
    return file_path

@pdf_bp.route('/export-pdf', methods=['POST'])
def export_pdf():
    """Generate comprehensive SLR parser PDF"""
    try:
        data = request.json
        
        # This function should be called from slr_service.py
        # We need to reconstruct the parser data from the grammar
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
        
        # Prepare parser data for PDF generation
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
        
        # Generate PDF
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

# Also keep the original simple function for backward compatibility
def generate_pdf(grammar, start_symbol, first, follow):
    """Simple PDF generator for FIRST/FOLLOW sets only"""
    file_name = f"grammar_notes_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join("/tmp", file_name)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    story = []

    # ---------- TITLE ----------
    story.append(Paragraph("<b>Compiler Design Notes</b>", styles["Title"]))
    story.append(Paragraph(
        "Grammar, FIRST and FOLLOW (Auto-generated)",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # ---------- INPUT GRAMMAR ----------
    story.append(Paragraph("<b>1. Input Grammar</b>", styles["Heading2"]))
    for nt, productions in grammar.items():
        for p in productions:
            story.append(Paragraph(f"{nt} → {p}", styles["Normal"]))

    story.append(Spacer(1, 12))

    # ---------- GRAMMAR INFO ----------
    story.append(Paragraph("<b>2. Grammar Definition</b>", styles["Heading2"]))
    story.append(Paragraph("Type: Context-Free Grammar (CFG)", styles["Normal"]))
    story.append(Paragraph(f"Start Symbol: {start_symbol}", styles["Normal"]))

    non_terminals = ", ".join(grammar.keys())
    story.append(Paragraph(f"Non-terminals: {{ {non_terminals} }}", styles["Normal"]))

    story.append(Spacer(1, 12))

    # ---------- FIRST ----------
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

    # ---------- FOLLOW ----------
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

    # ---------- SUMMARY TABLE ----------
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

    # ---------- EXAM NOTES ----------
    story.append(Paragraph("<b>6. Exam Notes</b>", styles["Heading2"]))
    story.append(Paragraph(
        "- FIRST helps in predicting derivations<br/>"
        "- FOLLOW defines valid symbols after a non-terminal<br/>"
        "- Used in LL(1) and SLR parsing",
        styles["Normal"]
    ))

    doc.build(story)
    return file_path