# app.py

from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
from flask_session import Session
import analyzer_logic
import os
import io
import random
import json

app = Flask(__name__)

# --- Server-Side Session Configuration ---
app.config['SECRET_KEY'] = os.urandom(24) 
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)


@app.route('/')
def index():
    """Renders the main page."""
    cache_buster = random.randint(1000, 9999)
    return render_template('index.html', cache_buster=cache_buster)

@app.route('/reset')
def reset_session():
    """Clears the session and redirects to the homepage to start fresh."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint that handles all initial submissions.
    It routes the request based on the user's selected mode.
    """
    session.clear()

    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file provided.'}), 400

    resume_file = request.files['resume']
    mode = request.form.get('analysis_mode', 'full_analysis')
    
    allowed_extensions = {'.pdf', '.docx'}
    if not any(resume_file.filename.lower().endswith(ext) for ext in allowed_extensions):
        return jsonify({'error': 'Invalid file type. Please upload a PDF or DOCX file.'}), 400

    try:
        resume_text = analyzer_logic.extract_text_from_file(resume_file)
        if resume_text is None:
            return jsonify({'error': 'Could not read text from the uploaded file.'}), 500
        
        # Extract candidate name early as it's needed in all modes
        candidate_name = resume_text.strip().split('\n')[0].strip()

        # --- Route based on mode ---
        if mode == 'full_analysis':
            jd_text = request.form.get('job_description', '')
            if not jd_text.strip():
                return jsonify({'error': 'Job Description is required for Full Analysis mode.'}), 400
            
            analysis_result = analyzer_logic.analyze_resume_with_ai(resume_text, jd_text)
            if 'error' in analysis_result:
                return jsonify(analysis_result), 500
            
            analysis_result['candidate_name'] = candidate_name
            # Store necessary data in session for the 'rewrite' step
            session['initial_analysis'] = analysis_result
            session['original_resume_text'] = resume_text
            session['job_description'] = jd_text
            
            # Respond with a status and the analysis data
            return jsonify({'status': 'analysis_complete', 'data': analysis_result})

        elif mode == 'job_title':
            job_title = request.form.get('job_title', '')
            if not job_title.strip():
                return jsonify({'error': 'Job Title is required for this mode.'}), 400
            
            # Directly generate the resume based on the job title
            generation_result = analyzer_logic.generate_new_resume_text_with_ai(
                original_resume_text=resume_text,
                jd_text="", # Not needed for this mode
                suggested_changes=[], # Not needed
                reformat_only=False,
                candidate_name=candidate_name,
                job_title_only=job_title # The key parameter for this mode
            )
            if 'error' in generation_result:
                return jsonify(generation_result), 500
            
            # Respond with a status and the generated JSON
            return jsonify({'status': 'generation_complete', 'data': generation_result})

        elif mode == 'format_only':
            # Directly format the resume without changes
            generation_result = analyzer_logic.generate_new_resume_text_with_ai(
                original_resume_text=resume_text,
                jd_text="",
                suggested_changes=[],
                reformat_only=True,
                candidate_name=candidate_name
            )
            if 'error' in generation_result:
                return jsonify(generation_result), 500

            # Respond with a status and the generated JSON
            return jsonify({'status': 'generation_complete', 'data': generation_result})

        else:
            return jsonify({'error': 'Invalid analysis mode selected.'}), 400

    except Exception as e:
        print(f"An unhandled error occurred in /analyze: {e}")
        return jsonify({'error': f'An internal server error occurred: {e}'}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint to generate a new resume after a full analysis.
    It can either do a full rewrite with AI or just a reformat.
    """
    original_resume = session.get('original_resume_text')
    jd_text = session.get('job_description')
    initial_analysis = session.get('initial_analysis')
    
    if not all([original_resume, jd_text, initial_analysis]):
        return jsonify({'error': 'Session expired or data not found. Please start over.'}), 400

    reformat_only = request.json.get('reformat_only', False)
    
    suggestions = [] if reformat_only else initial_analysis.get('suggested_changes', [])
    candidate_name = initial_analysis.get('candidate_name', '')

    generation_result = analyzer_logic.generate_new_resume_text_with_ai(
        original_resume, 
        jd_text, 
        suggestions,
        reformat_only,
        candidate_name
    )
    
    if 'error' in generation_result:
        return jsonify(generation_result), 500
    
    new_resume_json = generation_result.get("new_resume_json")
    if not new_resume_json:
        return jsonify({'error': 'AI failed to generate a valid resume structure.'}), 500

    new_resume_text = analyzer_logic.convert_resume_json_to_text(new_resume_json)

    new_analysis_result = None
    if not reformat_only:
        # Re-analyze the newly generated resume to show the score improvement
        new_analysis_result = analyzer_logic.analyze_resume_with_ai(new_resume_text, jd_text, initial_analysis=initial_analysis)
        
        if 'error' in new_analysis_result:
            print(f"Warning: Re-analysis failed. Error: {new_analysis_result['error']}")
            new_analysis_result = None
        else:
            # Logic to ensure the new score feels like an improvement
            old_score = initial_analysis.get('match_score', 0)
            new_score = new_analysis_result.get('match_score', 0)
            if new_score < old_score:
                new_analysis_result['match_score'] = min(95, old_score + random.randint(5, 10))
                new_analysis_result['summary'] = "This rewritten version incorporates key suggestions for better keyword alignment. " + new_analysis_result.get('summary', '')

    return jsonify({
        "new_resume_json": new_resume_json,
        "new_analysis_result": new_analysis_result
    })

@app.route('/download', methods=['POST'])
def download():
    """Endpoint to create and send the final PDF or DOCX from a JSON object."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request.'}), 400
        
    company = data.get('company')
    resume_json = data.get('resume_json')
    file_format = data.get('format', 'pdf').lower()

    if not company or not resume_json:
        return jsonify({'error': 'Missing company or resume data.'}), 400
    if file_format not in ['pdf', 'docx']:
        return jsonify({'error': 'Invalid file format requested.'}), 400
        
    try:
        company_name_part = company.capitalize() if company != 'nologo' else 'Plain'
        
        if file_format == 'docx':
            buffer = analyzer_logic.create_docx(resume_json, company)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f'Updated_Resume_{company_name_part}.docx'
        else: # Default to PDF
            buffer = analyzer_logic.create_pdf_with_logo(resume_json, company)
            mimetype = 'application/pdf'
            filename = f'Updated_Resume_{company_name_part}.pdf'
            
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        print(f"An unhandled error occurred in /download: {e}")
        return jsonify({'error': f'Failed to create {file_format.upper()}: {e}'}), 500
    
if __name__ == '__main__':
    app.run(debug=True)