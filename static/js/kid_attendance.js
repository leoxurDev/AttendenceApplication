// Kid Attendance & Star Confetti Engine

document.addEventListener('DOMContentLoaded', () => {
    // Canvas setup for Star/Circle particles
    initConfetti();

    // Student Roster Grid Listeners
    initStudentGrid();

    // Teacher Dashboard Controls
    initTeacherDashboard();

    // Unified Login Page Controller
    initUnifiedLogin();
});

// --- State Variables ---
let currentSelectedKidId = null;
let currentSelectedMood = 'happy';
let currentPIN = '';

// --- Student Grid Controller ---
function initStudentGrid() {
    const kidCards = document.querySelectorAll('.kid-card');
    const modal = document.getElementById('checkin-modal');
    
    // Screens
    const pinScreen = document.getElementById('pin-screen-container');
    const moodScreen = document.getElementById('mood-screen-container');
    
    // Modal buttons
    const closeBtn = document.getElementById('modal-close-btn');
    const pinCloseBtn = document.getElementById('pin-modal-close-btn');
    const submitBtn = document.getElementById('modal-submit-btn');
    
    // Names/Welcome text
    const welcomeText = document.getElementById('modal-welcome-text');
    const pinWelcomeText = document.getElementById('pin-modal-welcome-text');
    
    // Elements for PIN
    const pinDots = document.querySelectorAll('.pin-dot');
    const pinErrorMsg = document.getElementById('pin-error-msg');
    const keypadButtons = document.querySelectorAll('.keypad-btn');
    
    // Mood Buttons
    const moodButtons = document.querySelectorAll('.mood-option-btn');

    if (!modal) return; // Not on student grid screen

    function resetPINState() {
        currentPIN = '';
        pinDots.forEach(dot => dot.classList.remove('active'));
        if (pinErrorMsg) pinErrorMsg.classList.remove('show');
    }

    function showPINScreen() {
        if (pinScreen) pinScreen.style.display = 'block';
        if (moodScreen) moodScreen.style.display = 'none';
        resetPINState();
    }

    // Opening Check-in dialog
    kidCards.forEach(card => {
        card.addEventListener('click', () => {
            const kidName = card.getAttribute('data-name');
            currentSelectedKidId = card.getAttribute('data-id');
            
            if (pinWelcomeText) pinWelcomeText.textContent = `Hi, ${kidName}! 👋`;
            if (welcomeText) welcomeText.textContent = `Hi, ${kidName}! 👋`;
            
            // Set default mood styling
            moodButtons.forEach(btn => btn.classList.remove('selected'));
            const defaultMoodBtn = document.querySelector('.mood-option-btn[data-mood="happy"]');
            if (defaultMoodBtn) defaultMoodBtn.classList.add('selected');
            currentSelectedMood = 'happy';

            // Show modal and start with PIN screen
            showPINScreen();
            modal.classList.add('active');
        });
    });

    // Keypad interaction
    keypadButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const val = btn.getAttribute('data-val');
            const action = btn.getAttribute('data-action');

            if (val !== null) {
                if (currentPIN.length < 4) {
                    currentPIN += val;
                    updatePINDots();
                    if (currentPIN.length === 4) {
                        verifyPINCode();
                    }
                }
            } else if (action === 'clear') {
                resetPINState();
            } else if (action === 'backspace') {
                if (currentPIN.length > 0) {
                    currentPIN = currentPIN.slice(0, -1);
                    updatePINDots();
                }
            }
        });
    });

    function updatePINDots() {
        pinDots.forEach((dot, index) => {
            if (index < currentPIN.length) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    function verifyPINCode() {
        const formData = new FormData();
        formData.append('student_id', currentSelectedKidId);
        formData.append('pin_code', currentPIN);

        fetch(VERIFY_PIN_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // PIN is correct! Transition to mood screen
                if (pinScreen) pinScreen.style.display = 'none';
                if (moodScreen) moodScreen.style.display = 'block';
            } else {
                // PIN is wrong
                if (pinScreen) {
                    pinScreen.classList.add('shake');
                    if (pinErrorMsg) {
                        pinErrorMsg.textContent = data.error || 'Wrong PIN! 🤫';
                        pinErrorMsg.classList.add('show');
                    }
                    setTimeout(() => {
                        pinScreen.classList.remove('shake');
                    }, 500);
                }
                resetPINState();
            }
        })
        .catch(err => {
            console.error("PIN verification error:", err);
            resetPINState();
        });
    }

    // Mood picker choice click
    moodButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            moodButtons.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            currentSelectedMood = btn.getAttribute('data-mood');
        });
    });

    // Close Modal triggers
    const closeAllModals = () => {
        modal.classList.remove('active');
        currentSelectedKidId = null;
        resetPINState();
    };

    if (closeBtn) closeBtn.addEventListener('click', closeAllModals);
    if (pinCloseBtn) pinCloseBtn.addEventListener('click', closeAllModals);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeAllModals();
        }
    });

    // Check-in submit handler
    submitBtn.addEventListener('click', () => {
        if (!currentSelectedKidId) return;

        const formData = new FormData();
        formData.append('student_id', currentSelectedKidId);
        formData.append('status', 'present');
        formData.append('mood', currentSelectedMood);
        formData.append('checked_by', 'child');

        fetch(TOGGLE_ATTENDANCE_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Find student card and toggle visual highlight
                const card = document.querySelector(`.kid-card[data-id="${currentSelectedKidId}"]`);
                if (card) {
                    if (data.action === 'removed') {
                        card.classList.remove('checked-in');
                        card.querySelector('.status-indicator-badge').textContent = '🌙';
                        card.querySelector('.kid-status-text').innerHTML = 'Tap to check in!';
                    } else {
                        card.classList.add('checked-in');
                        card.querySelector('.status-indicator-badge').textContent = '☀️';
                        card.querySelector('.kid-status-text').innerHTML = `
                            Checked in at ${data.time} <br>
                            Feeling: ${data.mood_emoji}
                        `;
                        
                        // Fire star confetti particles centered on the student card!
                        const rect = card.getBoundingClientRect();
                        triggerConfetti(rect.left + rect.width / 2, rect.top + rect.height / 2);
                    }
                    
                    // Update header stat bars dynamically
                    recalculateGridStats();
                }
            } else {
                console.error("Check-in error:", data.error);
            }
            closeAllModals();
        })
        .catch(err => {
            console.error("Fetch Check-in failure:", err);
            closeAllModals();
        });
    });
}


// --- Dynamic Grid Statistics Recalculations ---
function recalculateGridStats() {
    const totalCards = document.querySelectorAll('.kid-card').length;
    const checkedInCount = document.querySelectorAll('.kid-card.checked-in').length;
    const rate = totalCards > 0 ? Math.round((checkedInCount / totalCards) * 100) : 0;

    // Update Banner Texts
    const statsHerePill = document.querySelector('.stats-cloud-banner .stat-pill:nth-child(2) strong');
    if (statsHerePill) statsHerePill.textContent = checkedInCount;

    const fillBar = document.querySelector('.progress-bar-fill');
    if (fillBar) fillBar.style.width = `${rate}%`;

    const percentText = document.querySelector('.progress-percent-text');
    if (percentText) percentText.textContent = `${rate}% Present`;
}

// --- Teacher Dashboard Controller ---
function initTeacherDashboard() {
    const actionBtns = document.querySelectorAll('.status-action-btn');

    actionBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const studentId = btn.getAttribute('data-student');
            const status = btn.getAttribute('data-status');
            
            const formData = new FormData();
            formData.append('student_id', studentId);
            formData.append('status', status);
            formData.append('checked_by', 'teacher');

            fetch(TOGGLE_ATTENDANCE_URL, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
                    if (row) {
                        // Deactivate all status buttons in this row
                        const rowBtns = row.querySelectorAll('.status-action-btn');
                        rowBtns.forEach(b => b.classList.remove('active'));

                        // Activate the target status button
                        const activeBtn = row.querySelector(`.status-action-btn[data-status="${data.status}"]`);
                        if (activeBtn) activeBtn.classList.add('active');

                        // Update Checked-in time cell
                        const timeCell = row.querySelector('.checked-time-cell');
                        if (timeCell) {
                            timeCell.textContent = (data.status !== 'absent') ? data.time : '-';
                        }

                        // Update Mood display cell
                        const moodCell = row.querySelector('.mood-cell');
                        if (moodCell) {
                            moodCell.textContent = (data.status !== 'absent' && data.mood_emoji) ? `${data.mood} ${data.mood_emoji}` : '-';
                        }

                        // Sparkle confetti effect on the clicked button if marked present
                        if (data.status === 'present') {
                            const rect = btn.getBoundingClientRect();
                            triggerConfetti(rect.left + rect.width / 2, rect.top + rect.height / 2);
                        }

                        // Recalculate Teacher Dashboard aggregate stats at top bar
                        recalculateTeacherStats();
                    }
                }
            })
            .catch(err => console.error("Teacher toggle failed:", err));
        });
    });
}

function recalculateTeacherStats() {
    const totalStudents = document.querySelectorAll('tr[data-student-id]').length;
    let presentCount = 0;
    let lateCount = 0;
    let absentCount = 0;

    document.querySelectorAll('tr[data-student-id]').forEach(row => {
        const activeBtn = row.querySelector('.status-action-btn.active');
        if (activeBtn) {
            const status = activeBtn.getAttribute('data-status');
            if (status === 'present') presentCount++;
            else if (status === 'late') lateCount++;
            else absentCount++;
        } else {
            absentCount++;
        }
    });

    const attendanceRate = totalStudents > 0 ? Math.round(((presentCount + lateCount) / totalStudents) * 100) : 0;

    // Update Top Metric Boxes
    const presentVal = document.querySelector('.mini-stat-card.present .value');
    if (presentVal) presentVal.textContent = presentCount;

    const lateVal = document.querySelector('.mini-stat-card.late .value');
    if (lateVal) lateVal.textContent = lateCount;

    const absentVal = document.querySelector('.mini-stat-card.absent .value');
    if (absentVal) absentVal.textContent = absentCount;

    const rateVal = document.querySelector('.mini-stat-card.rate .value');
    if (rateVal) rateVal.textContent = `${attendanceRate}%`;
}

// --- Confetti particle engine ---
let canvas = null;
let ctx = null;
let particles = [];
let animationId = null;

function initConfetti() {
    canvas = document.getElementById('confetti-canvas');
    if (!canvas) return;

    ctx = canvas.getContext('2d');
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();
}

class KidParticle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = Math.random() * 8 + 6;
        this.speedX = Math.random() * 12 - 6;
        this.speedY = Math.random() * -14 - 6; // Gravity thrust
        this.gravity = 0.45;
        
        // Soft kids themes colors
        this.colors = ['#ffafcc', '#bde0fe', '#a2d2ff', '#c7f9cc', '#fdf0d5', '#c8b6ff', '#fdeb8a'];
        this.color = this.colors[Math.floor(Math.random() * this.colors.length)];
        
        this.type = Math.random() > 0.5 ? 'star' : 'circle';
        this.rotation = Math.random() * 360;
        this.rotationSpeed = Math.random() * 12 - 6;
        this.opacity = 1;
        this.fade = Math.random() * 0.015 + 0.01;
    }
    update() {
        this.x += this.speedX;
        this.speedY += this.gravity;
        this.y += this.speedY;
        this.rotation += this.rotationSpeed;
        this.opacity -= this.fade;
    }
    draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate((this.rotation * Math.PI) / 180);
        ctx.fillStyle = this.color;
        ctx.globalAlpha = this.opacity;
        
        if (this.type === 'star') {
            // Draw a cute 5-point kid star
            ctx.beginPath();
            for (let i = 0; i < 5; i++) {
                ctx.lineTo(Math.cos((18 + i * 72) * Math.PI / 180) * this.size,
                           Math.sin((18 + i * 72) * Math.PI / 180) * this.size);
                ctx.lineTo(Math.cos((54 + i * 72) * Math.PI / 180) * (this.size / 2),
                           Math.sin((54 + i * 72) * Math.PI / 180) * (this.size / 2));
            }
            ctx.closePath();
            ctx.fill();
        } else {
            // Draw circle balloon confetti
            ctx.beginPath();
            ctx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
    }
}

function triggerConfetti(x, y) {
    if (!canvas) return;
    
    // Generate starburst particles
    for (let i = 0; i < 40; i++) {
        particles.push(new KidParticle(x, y));
    }
    if (!animationId) {
        animateParticles();
    }
}

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles = particles.filter(p => p.opacity > 0);
    
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    
    if (particles.length > 0) {
        animationId = requestAnimationFrame(animateParticles);
    } else {
        animationId = null;
    }
}

// --- Unified Login Controller ---
function initUnifiedLogin() {
    const tabStudent = document.getElementById('tab-student');
    const tabTeacher = document.getElementById('tab-teacher');
    const studentSection = document.getElementById('student-login-section');
    const teacherSection = document.getElementById('teacher-login-section');
    const slider = document.querySelector('.login-tab-slider');

    if (!tabStudent || !tabTeacher) return; // Not on unified login screen

    // Tab Switching Logic
    tabStudent.addEventListener('click', () => {
        tabStudent.classList.add('active');
        tabStudent.style.color = '#1e3a8a';
        tabTeacher.classList.remove('active');
        tabTeacher.style.color = '#475569';
        if (slider) slider.style.left = '0.35rem';
        if (studentSection) studentSection.style.display = 'block';
        if (teacherSection) teacherSection.style.display = 'none';
    });

    tabTeacher.addEventListener('click', () => {
        tabTeacher.classList.add('active');
        tabTeacher.style.color = '#1e3a8a';
        tabStudent.classList.remove('active');
        tabStudent.style.color = '#475569';
        if (slider) slider.style.left = 'calc(50% - 0.35rem)';
        if (teacherSection) teacherSection.style.display = 'block';
        if (studentSection) studentSection.style.display = 'none';
    });

    // Student Login State Variables
    let selectedStudentId = null;
    let selectedStudentName = '';
    let selectedStudentEmoji = '🎒';
    let selectedStudentColor = '#FDFFB6';
    let selectedMood = 'happy';
    let pinBuffer = '';

    const studentSelect = document.getElementById('student-select');
    const selectGroup = document.getElementById('student-select-group');
    const keypadContainer = document.getElementById('student-keypad-container');
    const moodContainer = document.getElementById('student-mood-container');
    const successContainer = document.getElementById('student-success-container');
    const moodWelcomeText = document.getElementById('student-mood-welcome');
    const pinDots = document.querySelectorAll('#student-keypad-container .pin-dot');
    const pinErrorMsg = document.getElementById('student-pin-error-msg');
    const keypadButtons = document.querySelectorAll('.keypad-btn.student-key');
    const moodButtons = document.querySelectorAll('#student-mood-container .mood-option-btn');
    const submitBtn = document.getElementById('student-submit-checkin');
    const resetBtn = document.getElementById('student-reset-btn');

    function resetStudentPIN() {
        pinBuffer = '';
        pinDots.forEach(dot => dot.classList.remove('active'));
        if (pinErrorMsg) pinErrorMsg.classList.remove('show');
    }

    // On Dropdown Change
    studentSelect.addEventListener('change', () => {
        const option = studentSelect.options[studentSelect.selectedIndex];
        selectedStudentId = studentSelect.value;
        selectedStudentName = option.getAttribute('data-name');
        selectedStudentEmoji = option.getAttribute('data-emoji') || '🎒';
        selectedStudentColor = option.getAttribute('data-color') || '#FDFFB6';

        resetStudentPIN();
        if (keypadContainer) keypadContainer.style.display = 'block';
        if (moodContainer) moodContainer.style.display = 'none';
        if (successContainer) successContainer.style.display = 'none';
    });

    // Keypad Logic
    keypadButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!selectedStudentId) return;

            const val = btn.getAttribute('data-val');
            const action = btn.getAttribute('data-action');

            if (val !== null) {
                if (pinBuffer.length < 4) {
                    pinBuffer += val;
                    updateDots();
                    if (pinBuffer.length === 4) {
                        verifyStudentPIN();
                    }
                }
            } else if (action === 'clear') {
                resetStudentPIN();
            } else if (action === 'backspace') {
                if (pinBuffer.length > 0) {
                    pinBuffer = pinBuffer.slice(0, -1);
                    updateDots();
                }
            }
        });
    });

    function updateDots() {
        pinDots.forEach((dot, idx) => {
            if (idx < pinBuffer.length) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    function verifyStudentPIN() {
        const formData = new FormData();
        formData.append('student_id', selectedStudentId);
        formData.append('pin_code', pinBuffer);

        fetch(VERIFY_PIN_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Success - hide selection dropdown and keypad
                if (selectGroup) selectGroup.style.display = 'none';
                if (keypadContainer) keypadContainer.style.display = 'none';
                if (moodWelcomeText) moodWelcomeText.textContent = `How are you feeling, ${selectedStudentName}?`;
                
                // Reset mood options highlight
                moodButtons.forEach(b => b.classList.remove('selected'));
                const defaultMoodBtn = document.querySelector('#student-mood-container .mood-option-btn[data-mood="happy"]');
                if (defaultMoodBtn) defaultMoodBtn.classList.add('selected');
                selectedMood = 'happy';
                
                if (moodContainer) moodContainer.style.display = 'block';
            } else {
                // Failed - Shake keypad container
                if (keypadContainer) {
                    keypadContainer.classList.add('shake');
                    if (pinErrorMsg) {
                        pinErrorMsg.textContent = data.error || 'Wrong PIN! 🤫';
                        pinErrorMsg.classList.add('show');
                    }
                    setTimeout(() => {
                        keypadContainer.classList.remove('shake');
                    }, 500);
                }
                resetStudentPIN();
            }
        })
        .catch(err => {
            console.error("Unified Login PIN error:", err);
            resetStudentPIN();
        });
    }

    // Mood Selector Choices
    moodButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            moodButtons.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedMood = btn.getAttribute('data-mood');
        });
    });

    // Check-in Submit Handler
    submitBtn.addEventListener('click', () => {
        if (!selectedStudentId) return;

        const formData = new FormData();
        formData.append('student_id', selectedStudentId);
        formData.append('status', 'present');
        formData.append('mood', selectedMood);
        formData.append('checked_by', 'child');

        fetch(TOGGLE_ATTENDANCE_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Show Success screen
                if (moodContainer) moodContainer.style.display = 'none';
                
                // Style Success Circle
                const successCircle = document.getElementById('student-success-avatar-circle');
                if (successCircle) {
                    successCircle.textContent = selectedStudentEmoji;
                    successCircle.style.backgroundColor = selectedStudentColor;
                }
                
                const successMsg = document.getElementById('student-success-msg');
                if (successMsg) {
                    successMsg.innerHTML = `<strong>${selectedStudentName}</strong> is checked in for today!<br>Feeling: ${data.mood_emoji} ${selectedMood.charAt(0).toUpperCase() + selectedMood.slice(1)}`;
                }

                if (successContainer) successContainer.style.display = 'block';

                // Confetti at center of page
                triggerConfetti(window.innerWidth / 2, window.innerHeight / 2 - 100);
            } else {
                console.error("Unified Login check-in failed:", data.error);
            }
        })
        .catch(err => console.error("Unified Login fetch check-in failed:", err));
    });

    // Reset Forms
    resetBtn.addEventListener('click', () => {
        studentSelect.value = '';
        if (selectGroup) selectGroup.style.display = 'block';
        if (keypadContainer) keypadContainer.style.display = 'none';
        if (moodContainer) moodContainer.style.display = 'none';
        if (successContainer) successContainer.style.display = 'none';
        resetStudentPIN();
    });
}

