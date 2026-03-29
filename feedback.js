// Star Rating System
document.addEventListener('DOMContentLoaded', function() {
    const stars = document.querySelectorAll('#starRating i');
    const ratingInput = document.getElementById('ratingValue');
    const ratingText = document.getElementById('ratingText');
    let currentRating = 0;

    stars.forEach(star => {
        star.addEventListener('mouseenter', function() {
            const rating = parseInt(this.getAttribute('data-rating'));
            highlightStars(rating);
        });

        star.addEventListener('mouseleave', function() {
            highlightStars(currentRating);
        });

        star.addEventListener('click', function() {
            currentRating = parseInt(this.getAttribute('data-rating'));
            ratingInput.value = currentRating;
            highlightStars(currentRating);
            
            const ratingMessages = {
                1: 'Poor - We can do better',
                2: 'Fair - Room for improvement',
                3: 'Good - Satisfied',
                4: 'Very Good - Happy with service',
                5: 'Excellent - Amazing experience!'
            };
            ratingText.textContent = ratingMessages[currentRating];
            ratingText.style.color = '#27AE60';
        });
    });

    function highlightStars(rating) {
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('active');
                star.classList.remove('far');
                star.classList.add('fas');
            } else {
                star.classList.remove('active');
                star.classList.remove('fas');
                star.classList.add('far');
            }
        });
    }
});

// Character Counter
const messageTextarea = document.getElementById('userMessage');
const charCountSpan = document.getElementById('charCount');

if (messageTextarea) {
    messageTextarea.addEventListener('input', function() {
        const count = this.value.length;
        charCountSpan.textContent = count;
        
        if (count > 500) {
            this.value = this.value.substring(0, 500);
            charCountSpan.textContent = 500;
            showToast('Maximum 500 characters allowed', 'error');
        }
    });
}

// Photo Upload Preview
const photoInput = document.getElementById('photoInput');
const photoPreview = document.getElementById('photoPreview');

if (photoInput) {
    photoInput.addEventListener('change', function(e) {
        photoPreview.innerHTML = '';
        const files = Array.from(e.target.files);
        
        files.forEach(file => {
            if (file.size > 5 * 1024 * 1024) {
                showToast(`File ${file.name} exceeds 5MB limit`, 'error');
                return;
            }
            
            if (!file.type.match('image.*')) {
                showToast(`File ${file.name} is not an image`, 'error');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                photoPreview.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    });
}

// Flag pour éviter les doubles soumissions
let isSubmitting = false;

// Submit Feedback - UNIQUE GESTIONNAIRE
async function submitFeedback(event) {
    event.preventDefault();
    
    // Empêcher les doubles soumissions
    if (isSubmitting) {
        console.log('Soumission déjà en cours...');
        return;
    }
    
    isSubmitting = true;
    
    // Get form values
    const rating = document.getElementById('ratingValue').value;
    const name = document.getElementById('userName').value.trim();
    const email = document.getElementById('userEmail').value.trim();
    const service = document.getElementById('serviceType').value;
    const feedbackType = document.querySelector('input[name="feedbackType"]:checked').value;
    const message = document.getElementById('userMessage').value.trim();
    const consent = document.getElementById('consent').checked;
    
    // Validation
    if (!rating) {
        showToast('Please select a rating', 'error');
        isSubmitting = false;
        return;
    }
    
    if (!name) {
        showToast('Please enter your name', 'error');
        isSubmitting = false;
        return;
    }
    
    if (!email) {
        showToast('Please enter your email', 'error');
        isSubmitting = false;
        return;
    }
    
    if (!isValidEmail(email)) {
        showToast('Please enter a valid email address', 'error');
        isSubmitting = false;
        return;
    }
    
    if (!service) {
        showToast('Please select a service', 'error');
        isSubmitting = false;
        return;
    }
    
    if (!message) {
        showToast('Please enter your feedback message', 'error');
        isSubmitting = false;
        return;
    }
    
    if (message.length < 20) {
        showToast('Please provide more details (minimum 20 characters)', 'error');
        isSubmitting = false;
        return;
    }
    
    if (!consent) {
        showToast('Please consent to publishing your testimonial', 'error');
        isSubmitting = false;
        return;
    }
    
    // Prepare data for submission
    const feedbackData = {
        rating: parseInt(rating),
        name: name,
        email: email,
        service: service,
        feedbackType: feedbackType,
        message: message,
        date: new Date().toISOString(),
        status: 'pending'
    };
    
    try {
        // Simulate API call
        await simulateApiCall(feedbackData);
        
        // Store in localStorage for demo
        let allFeedback = JSON.parse(localStorage.getItem('userFeedback') || '[]');
        allFeedback.push(feedbackData);
        localStorage.setItem('userFeedback', JSON.stringify(allFeedback));
        
        // Show success message
        showToast('Thank you for your feedback! Your story helps others.', 'success');
        
        // Reset form
        document.getElementById('feedbackForm').reset();
        document.getElementById('ratingValue').value = '';
        document.getElementById('ratingText').textContent = 'Select rating';
        document.getElementById('ratingText').style.color = '#666';
        document.getElementById('charCount').textContent = '0';
        
        // Clear photo preview
        if (photoPreview) {
            photoPreview.innerHTML = '';
        }
        
        // Reset stars
        const stars = document.querySelectorAll('#starRating i');
        stars.forEach(star => {
            star.classList.remove('active', 'fas');
            star.classList.add('far');
        });
        
        // Reset current rating variable
        window.currentRating = 0;
        
        // Ajouter le nouveau témoignage UNE SEULE FOIS
        if (feedbackData.feedbackType === 'testimonial') {
            addTestimonialToGrid(feedbackData);
        }
        
    } catch (error) {
        showToast('Something went wrong. Please try again.', 'error');
        console.error('Error:', error);
    } finally {
        // Réactiver après 2 secondes pour éviter le spam
        setTimeout(() => {
            isSubmitting = false;
        }, 2000);
    }
}

// Simulate API call
function simulateApiCall(data) {
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log('Feedback submitted:', data);
            resolve();
        }, 1000);
    });
}

// Add testimonial to grid dynamically - UNE SEULE FOIS
function addTestimonialToGrid(feedbackData) {
    // Vérifier que c'est bien un témoignage
    if (feedbackData.feedbackType !== 'testimonial') return;
    
    const testimonialsGrid = document.getElementById('testimonialsGrid');
    
    // Vérifier si le témoignage existe déjà pour éviter les doublons
    const existingTestimonials = testimonialsGrid.querySelectorAll('.testimonial-card');
    let isDuplicate = false;
    
    existingTestimonials.forEach(card => {
        const cardName = card.querySelector('.user-info h4')?.textContent;
        const cardMessage = card.querySelector('.testimonial-text')?.textContent;
        if (cardName === feedbackData.name && cardMessage === `"${feedbackData.message.substring(0, 150)}${feedbackData.message.length > 150 ? '...' : ''}"`) {
            isDuplicate = true;
        }
    });
    
    if (isDuplicate) {
        console.log('Testimonial already exists, skipping...');
        return;
    }
    
    const testimonialHTML = `
        <div class="testimonial-card fade-in">
            <div class="testimonial-header">
                <div class="user-avatar">
                    <img src="https://randomuser.me/api/portraits/${Math.random() > 0.5 ? 'women' : 'men'}/${Math.floor(Math.random() * 100)}.jpg" alt="${feedbackData.name}">
                </div>
                <div class="user-info">
                    <h4>${escapeHtml(feedbackData.name)}</h4>
                    <div class="rating">
                        ${'<i class="fas fa-star"></i>'.repeat(feedbackData.rating)}
                        ${'<i class="far fa-star"></i>'.repeat(5 - feedbackData.rating)}
                    </div>
                    <span class="service-tag">${escapeHtml(getServiceName(feedbackData.service))}</span>
                </div>
            </div>
            <p class="testimonial-text">"${escapeHtml(feedbackData.message.substring(0, 150))}${feedbackData.message.length > 150 ? '...' : ''}"</p>
            <div class="testimonial-footer">
                <span class="date">Just now</span>
                <i class="fas fa-quote-right"></i>
            </div>
        </div>
    `;
    
    testimonialsGrid.insertAdjacentHTML('afterbegin', testimonialHTML);
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Get service name from value
function getServiceName(serviceValue) {
    const services = {
        'consultation': 'Online Consultation',
        'diet-plan': 'Personalized Diet Plan',
        'ai-tracker': 'AI Calorie Tracker',
        'blog': 'Blog & Resources',
        'multiple': 'Multiple Services'
    };
    return services[serviceValue] || serviceValue;
}

// Validate email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('notificationToast');
    toast.textContent = message;
    toast.className = `toast-notification ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Load more testimonials
let testimonialPage = 1;

function loadMoreTestimonials() {
    // Simulate loading more testimonials from API
    const moreTestimonials = [
        {
            name: "Fatima Z.",
            rating: 5,
            service: "Hormonal Balance",
            message: "The personalized approach to my PCOS changed my life. Finally found something that works!",
            date: "March 2026"
        },
        {
            name: "Karim B.",
            rating: 4,
            service: "Weight Management",
            message: "Great program with excellent support. Lost 10kg in 4 months sustainably.",
            date: "February 2026"
        }
    ];
    
    const testimonialsGrid = document.getElementById('testimonialsGrid');
    
    moreTestimonials.forEach(testimonial => {
        const testimonialHTML = `
            <div class="testimonial-card fade-in">
                <div class="testimonial-header">
                    <div class="user-avatar">
                        <img src="https://randomuser.me/api/portraits/${Math.random() > 0.5 ? 'women' : 'men'}/${Math.floor(Math.random() * 100)}.jpg" alt="${testimonial.name}">
                    </div>
                    <div class="user-info">
                        <h4>${testimonial.name}</h4>
                        <div class="rating">
                            ${'<i class="fas fa-star"></i>'.repeat(testimonial.rating)}
                            ${'<i class="far fa-star"></i>'.repeat(5 - testimonial.rating)}
                        </div>
                        <span class="service-tag">${testimonial.service}</span>
                    </div>
                </div>
                <p class="testimonial-text">"${testimonial.message}"</p>
                <div class="testimonial-footer">
                    <span class="date">${testimonial.date}</span>
                    <i class="fas fa-quote-right"></i>
                </div>
            </div>
        `;
        testimonialsGrid.insertAdjacentHTML('beforeend', testimonialHTML);
    });
    
    // Show message when no more testimonials
    testimonialPage++;
    if (testimonialPage > 2) {
        const viewMoreBtn = document.querySelector('.view-more-btn');
        viewMoreBtn.disabled = true;
        viewMoreBtn.style.opacity = '0.5';
        viewMoreBtn.innerHTML = '<span>No More Stories</span>';
        showToast('You\'ve seen all testimonials!', 'success');
    }
}

// Newsletter subscription
function handleNewsletter(event) {
    event.preventDefault();
    const email = event.target.querySelector('input').value;
    
    if (isValidEmail(email)) {
        showToast(`✨ Thank you for subscribing! You'll receive weekly wellness insights at ${email}`, 'success');
        event.target.reset();
    } else {
        showToast('Please enter a valid email address', 'error');
    }
}

// Mobile menu toggle
function toggleMenu() {
    const nav = document.getElementById('navMenu');
    nav.classList.toggle('active');
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.testimonial-card, .gallery-item').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease-out';
    observer.observe(el);
});

// UNIQUE GESTIONNAIRE DE SOUMISSION - Plus de double appel
const feedbackForm = document.getElementById('feedbackForm');
if (feedbackForm) {
    feedbackForm.addEventListener('submit', submitFeedback);
}