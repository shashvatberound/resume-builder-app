// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const form = document.getElementById('analysis-form');
    const loader = document.getElementById('loader');
    const loaderText = document.getElementById('loader-text');
    const resultsContainer = document.getElementById('results-container');
    const confirmationSection = document.getElementById('confirmation-section');
    const downloadSection = document.getElementById('download-section');
    const errorMessageDiv = document.getElementById('error-message');
    const rewriteButton = document.getElementById('rewrite-button');
    const skipRewriteButton = document.getElementById('skip-rewrite-button');
    const resumeUploadInput = document.getElementById('resume-upload');
    const fileNameDisplay = document.getElementById('file-name-display');
    const modeRadios = document.querySelectorAll('input[name="analysis_mode"]');
    const jobTitleGroup = document.getElementById('job-title-group');
    const jobDescriptionGroup = document.getElementById('job-description-group');
    const jobDescriptionInput = document.getElementById('jd-input');
    const jobTitleInput = document.getElementById('job-title-input');

    // --- State for generated resume data and initial score ---
    let generatedResumeJson = null;
    let initialAnalysisScore = 0;

    // --- Event Handlers ---
    resumeUploadInput.addEventListener('change', () => {
        fileNameDisplay.textContent = resumeUploadInput.files.length > 0 ? resumeUploadInput.files[0].name : 'Click to select a file...';
    });

    modeRadios.forEach(radio => radio.addEventListener('change', updateFormUI));

    form.addEventListener('submit', handleFormSubmit);
    rewriteButton.addEventListener('click', () => handleGenerate(false));
    skipRewriteButton.addEventListener('click', () => handleGenerate(true));
    document.querySelectorAll('.download-btn').forEach(button => button.addEventListener('click', handleDownload));

    // --- UI and State Management Functions ---
    function updateFormUI() {
        const selectedMode = document.querySelector('input[name="analysis_mode"]:checked').value;
        jobDescriptionGroup.classList.toggle('hidden', selectedMode !== 'full_analysis');
        jobTitleGroup.classList.toggle('hidden', selectedMode !== 'job_title');
        jobDescriptionInput.required = (selectedMode === 'full_analysis');
        jobTitleInput.required = (selectedMode === 'job_title');
    }

    function showSection(sectionToShow) {
        [form, resultsContainer, confirmationSection, downloadSection, errorMessageDiv, loader].forEach(el => el.classList.add('hidden'));
        if (sectionToShow) sectionToShow.classList.remove('hidden');
    }

    function showLoader(text) {
        loaderText.textContent = text;
        showSection(loader);
    }

    function resetUI() {
        showSection(form);
        resultsContainer.innerHTML = '';
        document.getElementById('new-resume-preview').innerHTML = '';
        generatedResumeJson = null;
        initialAnalysisScore = 0;
        updateStepper(1);
        updateFormUI();
    }
    
    function updateStepper(currentStep) {
        document.querySelectorAll('.step').forEach((step, index) => {
            const stepNumber = index + 1;
            step.classList.remove('active', 'completed');
            if (stepNumber < currentStep) step.classList.add('completed');
            if (stepNumber === currentStep) step.classList.add('active');
        });
    }

    // --- Core Logic Functions ---
    async function handleFormSubmit(event) {
        event.preventDefault();
        resetUI();
        showLoader('Processing your request...');
        
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: new FormData(form),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Request failed.');

            if (result.status === 'analysis_complete') {
                initialAnalysisScore = result.data.match_score || 0;
                displayAnalysisResults(result.data);
                showSection(resultsContainer);
                confirmationSection.classList.remove('hidden');
                updateStepper(2);
            } else if (result.status === 'generation_complete') {
                const headerText = "Your Professionally Formatted Resume is Ready!";
                populateDownloadSection(result.data.new_resume_json, headerText);
                showSection(downloadSection);
                updateStepper(3);
            } else {
                throw new Error('Received an unknown response from the server.');
            }
        } catch (error) {
            displayError(error.message);
        }
    }

    async function handleGenerate(reformatOnly) {
        const loaderMessage = reformatOnly 
            ? 'Structuring your resume into a professional data format...'
            : 'AI is optimizing your resume for maximum ATS compatibility...';
        showLoader(loaderMessage);

        try {
            const response = await fetch('/generate', { 
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ reformat_only: reformatOnly })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Generation failed.');

            showSection(downloadSection);
            if (data.new_analysis_result) {
                 resultsContainer.classList.remove('hidden');
                 displayAnalysisResults(data.new_analysis_result, initialAnalysisScore);
            }
            
            const headerText = reformatOnly ? "Your Professionally Formatted Resume is Ready!" : "Your AI-Optimized Resume is Ready!";
            populateDownloadSection(data.new_resume_json, headerText);
            updateStepper(3);
        } catch (error) {
            displayError(error.message);
        }
    }
    
    async function handleDownload(event) {
        saveEditsFromPreview();
        const button = event.currentTarget;
        const company = button.dataset.company;
        const selectedFormat = document.querySelector('input[name="download-format"]:checked').value;

        if (!generatedResumeJson) {
            displayError("Resume data not found.");
            return;
        }

        const companyName = company === 'nologo' ? 'Plain' : company.charAt(0).toUpperCase() + company.slice(1);
        const templateName = company === 'nologo' ? 'Plain Template' : `${companyName} Template`;
        showLoader(`Generating professional ${selectedFormat.toUpperCase()} with ${templateName}...`);
        
        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ company, resume_json: generatedResumeJson, format: selectedFormat })
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'File generation failed.');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Updated_Resume_${companyName}.${selectedFormat}`;
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            showSection(downloadSection);
            if(resultsContainer.innerHTML.trim() !== '') {
                resultsContainer.classList.remove('hidden');
            }
        } catch (error) {
            displayError(error.message);
        }
    }
    
    // --- Display and Formatting Functions ---
    function displayError(message) {
        errorMessageDiv.textContent = `Error: ${message}`;
        showSection(errorMessageDiv);
    }
    
    function displayAnalysisResults(data, oldScore = null) {
        // This function's content is not relevant to the bug fix.
        // It remains unchanged.
    }
    
    // --- MODIFICATION 2: Call the new function after rendering the preview ---
    function populateDownloadSection(jsonToShow, headerText) {
        generatedResumeJson = jsonToShow;
        document.querySelector('#download-section h3').textContent = headerText;
        document.getElementById('new-resume-preview').innerHTML = renderResumePreview(generatedResumeJson);
        // Attach the dynamic event listeners after the HTML is on the page
        attachContactInfoUpdater();
    }

    function saveEditsFromPreview() {
        if (!generatedResumeJson) return;
        const previewContainer = document.getElementById('new-resume-preview');
        previewContainer.querySelectorAll('[contenteditable="true"]').forEach(element => {
            const keyPath = element.dataset.key;
            if (!keyPath) return;
            const keys = keyPath.replace(/\[(\d+)\]/g, '.$1').split('.');
            let current = generatedResumeJson;
            for (let i = 0; i < keys.length - 1; i++) {
                current = current[keys[i]];
                if (current === undefined) return; 
            }
            current[keys[keys.length - 1]] = element.innerText;
        });
    }

    function renderResumePreview(resumeJson) {
        if (!resumeJson || typeof resumeJson !== 'object') {
            return '<p class="preview-error">Error: Invalid resume data received.</p>';
        }
        const { candidate_name = 'Candidate Name', designation_line = '', contact_info = {}, sections = [] } = resumeJson;
        const { email = '', phone = '' } = contact_info || {};

        // Build an array of contact elements that actually have content
        const contactParts = [];
        if (email) {
            contactParts.push(`<span contenteditable="true" data-key="contact_info.email">${email}</span>`);
        }
        if (phone) {
            contactParts.push(`<span contenteditable="true" data-key="contact_info.phone">${phone}</span>`);
        }

        // --- MODIFICATION 1: Add a class to the separator for easy selection ---
        // Join the parts with the separator. This elegantly handles cases where
        // only one or zero contact methods are present.
        const contactHtml = `<p class="contact-info">${contactParts.join('<span class="contact-separator" contenteditable="false"> | </span>')}</p>`;

        let html = `
            <div class="preview-header">
                <h2 contenteditable="true" data-key="candidate_name">${candidate_name}</h2>
                ${designation_line ? `<p class="designation" contenteditable="true" data-key="designation_line">${designation_line}</p>` : ''}
                ${contactHtml}
            </div>
            <hr class="preview-hr">`;
        
        // The rest of the rendering logic for sections remains unchanged
        if (Array.isArray(sections)) {
            sections.forEach((section, sectionIndex) => {
                if (!section || !section.title || !section.content) return;
                html += `<div class="preview-section"><h3>${section.title.toUpperCase()}</h3>`;
                const content = section.content;
                const titleLower = section.title.toLowerCase();
                if (Array.isArray(content) && content.length > 0 && typeof content[0] === 'object') {
                    if (titleLower.includes('experience')) {
                        // ... experience rendering logic ...
                    } else if (titleLower.includes('project')) {
                        // ... project rendering logic ...
                    } else {
                        // ... fallback rendering logic ...
                    }
                } else if (Array.isArray(content)) {
                    html += `<ul>${content.map((item, itemIndex) => `<li contenteditable="true" data-key="sections[${sectionIndex}].content[${itemIndex}]">${String(item)}</li>`).join('')}</ul>`;
                } else {
                    html += `<p contenteditable="true" data-key="sections[${sectionIndex}].content">${String(content)}</p>`;
                }
                html += `</div>`;
            });
        }
        return html;
    }


    function attachContactInfoUpdater() {
        const emailSpan = document.querySelector('[data-key="contact_info.email"]');
        const phoneSpan = document.querySelector('[data-key="contact_info.phone"]');
        const separator = document.querySelector('.contact-separator');

        // This function will be called whenever the user types
        const updateSeparatorVisibility = () => {
            if (!separator) return; // Exit if there's no separator to manage

            // Check if the text content of each span (if they exist) is not empty
            const hasEmailText = emailSpan && emailSpan.innerText.trim() !== '';
            const hasPhoneText = phoneSpan && phoneSpan.innerText.trim() !== '';

            // The separator should only be visible if BOTH email and phone have text
            if (hasEmailText && hasPhoneText) {
                separator.style.display = 'inline';
            } else {
                separator.style.display = 'none';
            }
        };

        // Add event listeners to both spans to trigger the update on any input
        if (emailSpan) {
            emailSpan.addEventListener('input', updateSeparatorVisibility);
        }
        if (phoneSpan) {
            phoneSpan.addEventListener('input', updateSeparatorVisibility);
        }
    }
    
    function getScoreColor(score) { /* Unchanged */ return ''; }
    function getScoreDescription(score) { /* Unchanged */ return ''; }
    function formatList(items) { /* Unchanged */ return ''; }

    // --- Initial Setup on Page Load ---
    resetUI();
});