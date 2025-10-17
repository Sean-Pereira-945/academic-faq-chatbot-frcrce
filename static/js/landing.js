// Landing page animations using anime.js

document.addEventListener('DOMContentLoaded', function() {
    // Animate hero title
    anime({
        targets: '.hero-title',
        opacity: [0, 1],
        translateY: [30, 0],
        duration: 1000,
        easing: 'easeOutExpo'
    });

    // Animate hero subtitle
    anime({
        targets: '.hero-subtitle',
        opacity: [0, 1],
        translateY: [30, 0],
        duration: 1000,
        delay: 200,
        easing: 'easeOutExpo'
    });

    // Animate hero buttons
    anime({
        targets: '.hero-buttons a',
        opacity: [0, 1],
        translateY: [30, 0],
        duration: 1000,
        delay: anime.stagger(100, {start: 400}),
        easing: 'easeOutExpo'
    });

    // Animate stats
    anime({
        targets: '.stat-item',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
        delay: anime.stagger(100, {start: 600}),
        easing: 'easeOutExpo'
    });

    // Animate floating cards
    anime({
        targets: '.floating-card',
        opacity: [0, 1],
        scale: [0.8, 1],
        duration: 1200,
        delay: anime.stagger(200, {start: 800}),
        easing: 'easeOutElastic(1, .8)'
    });

    // Animate feature cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                anime({
                    targets: entry.target,
                    opacity: [0, 1],
                    translateY: [50, 0],
                    duration: 800,
                    easing: 'easeOutExpo'
                });
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        observer.observe(card);
    });

    // Observe tech cards
    document.querySelectorAll('.tech-card').forEach(card => {
        observer.observe(card);
    });

    // Smooth scroll for navigation links
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

    // Navbar background on scroll
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar');

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            navbar.style.background = 'rgba(0, 0, 0, 0.95)';
        } else {
            navbar.style.background = 'rgba(0, 0, 0, 0.8)';
        }

        lastScroll = currentScroll;
    });

    // Animate stats numbers
    const animateValue = (element, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = value + (end >= 1000 ? '+' : '%');
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };

    // Observe stats for animation
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statNumber = entry.target;
                const finalValue = parseInt(statNumber.textContent);
                if (!isNaN(finalValue)) {
                    animateValue(statNumber, 0, finalValue, 2000);
                }
                statsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    // Track mouse movement for subtle parallax effect
    document.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;

        anime({
            targets: '.orb-1',
            translateX: mouseX * 30,
            translateY: mouseY * 30,
            duration: 1000,
            easing: 'easeOutQuad'
        });

        anime({
            targets: '.orb-2',
            translateX: mouseX * -20,
            translateY: mouseY * -20,
            duration: 1200,
            easing: 'easeOutQuad'
        });
    });

    // Feature card hover animation
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            anime({
                targets: this.querySelector('.feature-icon'),
                scale: [1, 1.2],
                rotate: [0, 5],
                duration: 300,
                easing: 'easeOutElastic(1, .6)'
            });
        });

        card.addEventListener('mouseleave', function() {
            anime({
                targets: this.querySelector('.feature-icon'),
                scale: [1.2, 1],
                rotate: [5, 0],
                duration: 300,
                easing: 'easeOutElastic(1, .6)'
            });
        });
    });

    // Button hover effects
    document.querySelectorAll('.primary-button, .cta-button-large').forEach(button => {
        button.addEventListener('mouseenter', function() {
            anime({
                targets: this.querySelector('svg'),
                translateX: [0, 5],
                duration: 300,
                easing: 'easeOutQuad'
            });
        });

        button.addEventListener('mouseleave', function() {
            anime({
                targets: this.querySelector('svg'),
                translateX: [5, 0],
                duration: 300,
                easing: 'easeOutQuad'
            });
        });
    });

    // Continuous floating animation for hero cards
    setInterval(() => {
        anime({
            targets: '.floating-card',
            translateY: [
                { value: -15, duration: 2000, easing: 'easeInOutSine' },
                { value: 0, duration: 2000, easing: 'easeInOutSine' }
            ],
            loop: false
        });
    }, 4000);

    // Pulse animation for orbs
    anime({
        targets: '.orb',
        scale: [1, 1.1, 1],
        opacity: [0.2, 0.3, 0.2],
        duration: 4000,
        easing: 'easeInOutSine',
        loop: true
    });

    console.log('Landing page animations initialized');
});
