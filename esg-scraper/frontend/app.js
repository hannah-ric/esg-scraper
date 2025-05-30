// ESG Analyzer Frontend Application
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://api.esg-analyzer.com';

// Utility functions
function scrollToAnalyze() {
    document.getElementById('analyze').scrollIntoView({ behavior: 'smooth' });
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showResults() {
    document.getElementById('results').classList.remove('hidden');
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

// Animate score circles
function animateScore(elementId, score, color) {
    const circle = document.getElementById(elementId);
    const scoreElement = document.getElementById(elementId.replace('Circle', 'Score'));
    
    // Calculate stroke offset (lower offset = more filled)
    const offset = 351.86 - (351.86 * score / 100);
    
    // Animate the circle
    circle.style.transition = 'stroke-dashoffset 1s ease-out';
    circle.style.strokeDashoffset = offset;
    
    // Animate the score number
    let currentScore = 0;
    const increment = score / 50;
    const timer = setInterval(() => {
        currentScore += increment;
        if (currentScore >= score) {
            currentScore = score;
            clearInterval(timer);
        }
        scoreElement.textContent = Math.round(currentScore);
    }, 20);
}

// Display insights
function displayInsights(insights) {
    const container = document.getElementById('insights');
    container.innerHTML = '';
    
    insights.forEach(insight => {
        const div = document.createElement('div');
        div.className = 'flex items-start space-x-3 p-4 bg-purple-50 rounded-lg';
        div.innerHTML = `
            <svg class="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <p class="text-gray-700">${insight}</p>
        `;
        container.appendChild(div);
    });
}

// Display greenwashing assessment
function displayGreenwashing(assessment) {
    if (!assessment) return;
    
    const section = document.getElementById('greenwashingSection');
    const content = document.getElementById('greenwashingContent');
    
    section.classList.remove('hidden');
    
    const riskColors = {
        low: 'green',
        medium: 'yellow',
        high: 'red'
    };
    
    const riskColor = riskColors[assessment.risk_level] || 'gray';
    
    content.innerHTML = `
        <div class="mb-6">
            <div class="flex items-center justify-between mb-4">
                <span class="text-lg font-semibold">Risk Level</span>
                <span class="px-4 py-2 bg-${riskColor}-100 text-${riskColor}-800 rounded-full font-semibold">
                    ${assessment.risk_level.toUpperCase()}
                </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-3">
                <div class="bg-${riskColor}-500 h-3 rounded-full transition-all duration-1000" 
                     style="width: ${assessment.risk_score * 100}%"></div>
            </div>
        </div>
        
        <div class="mb-6">
            <h4 class="font-semibold text-gray-800 mb-3">Risk Indicators</h4>
            <div class="space-y-2">
                ${Object.entries(assessment.indicators || {}).map(([key, value]) => `
                    <div class="flex items-center justify-between">
                        <span class="text-gray-600">${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                        <span class="font-semibold ${value > 0 ? 'text-red-600' : 'text-green-600'}">${value}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="p-4 bg-blue-50 rounded-lg">
            <p class="text-blue-800">${assessment.recommendation}</p>
        </div>
    `;
}

// Display framework coverage
function displayFrameworkCoverage(coverage) {
    const container = document.getElementById('frameworkCoverage');
    container.innerHTML = '';
    
    coverage.forEach(framework => {
        const div = document.createElement('div');
        div.className = 'bg-white p-6 rounded-lg border border-gray-200';
        
        const coverageColor = framework.coverage_percentage >= 70 ? 'green' : 
                            framework.coverage_percentage >= 40 ? 'yellow' : 'red';
        
        div.innerHTML = `
            <div class="flex items-center justify-between mb-4">
                <h4 class="text-lg font-semibold text-gray-800">${framework.framework}</h4>
                <span class="text-2xl font-bold text-${coverageColor}-600">${framework.coverage_percentage}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div class="bg-${coverageColor}-500 h-2 rounded-full transition-all duration-1000" 
                     style="width: ${framework.coverage_percentage}%"></div>
            </div>
            <div class="text-sm text-gray-600">
                <p>Requirements Met: ${framework.requirements_met} / ${framework.total_requirements}</p>
            </div>
        `;
        
        container.appendChild(div);
    });
}

// Handle form submission
document.getElementById('analysisForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get form data
    const content = document.getElementById('content').value;
    const companyName = document.getElementById('companyName').value;
    const analysisType = document.getElementById('analysisType').value;
    
    // Get selected frameworks
    const frameworks = [];
    document.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        frameworks.push(cb.value);
    });
    
    // Determine endpoint and options based on analysis type
    let endpoint = '/api/analyze';
    let useBert = false;
    
    if (analysisType === 'standard' || analysisType === 'deep') {
        endpoint = '/api/v2/bert/analyze';
        useBert = true;
    }
    
    // Show loading
    showLoading();
    
    try {
        // Make API request
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Add auth header if you have authentication
                // 'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                content,
                company_name: companyName,
                frameworks,
                use_bert: useBert,
                analysis_depth: analysisType,
                extract_metrics: true
            })
        });
        
        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Hide loading
        hideLoading();
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        hideLoading();
        alert(`Error: ${error.message}`);
        console.error('Analysis error:', error);
    }
});

// Display all results
function displayResults(data) {
    // Animate scores
    setTimeout(() => {
        animateScore('envCircle', data.scores.environmental || 0);
        animateScore('socCircle', data.scores.social || 0);
        animateScore('govCircle', data.scores.governance || 0);
    }, 100);
    
    // Display insights
    if (data.insights && data.insights.length > 0) {
        displayInsights(data.insights);
    }
    
    // Display greenwashing assessment (if BERT analysis)
    if (data.greenwashing_assessment) {
        displayGreenwashing(data.greenwashing_assessment);
    }
    
    // Display framework coverage
    if (data.framework_coverage && data.framework_coverage.length > 0) {
        displayFrameworkCoverage(data.framework_coverage);
    }
    
    // Show results section
    showResults();
}

// Add sample data for testing
function loadSampleData() {
    document.getElementById('content').value = `
Our company has achieved significant progress in environmental sustainability. 
We reduced carbon emissions by 35% compared to 2020 baseline through renewable energy adoption.
Water consumption decreased by 25% through efficiency improvements.
Employee safety improved with TRIR of 0.5, down from 1.2 last year.
Board diversity increased to 40% female directors.
We invested $2M in community development programs.
Target: Net zero emissions by 2040 with science-based targets.
    `.trim();
    
    document.getElementById('companyName').value = 'Sample Corp';
}

// Add event listener for demo button if needed
document.addEventListener('DOMContentLoaded', () => {
    // Check if there's a demo button
    const demoButton = document.getElementById('demoButton');
    if (demoButton) {
        demoButton.addEventListener('click', loadSampleData);
    }
}); 