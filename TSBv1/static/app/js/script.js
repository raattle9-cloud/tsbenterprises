// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    if (menuBtn && mobileMenu) {
      menuBtn.addEventListener('click', function() {
        mobileMenu.classList.toggle('open');
      });
      // Optional: close menu when clicking outside
      document.addEventListener('click', function(e) {
        if (!mobileMenu.contains(e.target) && !menuBtn.contains(e.target)) {
          mobileMenu.classList.remove('open');
        }
      });
    }
  
    // Sync navbar animation delays (including dropdown support link)
    const desktopNavLinks = document.querySelectorAll('.site-header .nav-left .nav-link');
    if (desktopNavLinks.length) {
      const baseDelay = 0.2;
      desktopNavLinks.forEach((link, index) => {
        const delay = (index + 1) * baseDelay;
        link.style.animationDelay = `${delay}s`;
      });
    }
  });
  // Mobile menu toggle
  document.addEventListener('DOMContentLoaded', function() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    if (menuBtn && mobileMenu) {
      menuBtn.addEventListener('click', function() {
        mobileMenu.classList.toggle('open');
      });
      // Optional: close menu when clicking outside
      document.addEventListener('click', function(e) {
        if (!mobileMenu.contains(e.target) && !menuBtn.contains(e.target)) {
          mobileMenu.classList.remove('open');
        }
      });
    }
  });
  // Mobile menu toggle
  document.addEventListener('DOMContentLoaded', function() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    if (menuBtn && mobileMenu) {
      menuBtn.addEventListener('click', function() {
        mobileMenu.classList.toggle('open');
      });
      // Optional: close menu when clicking outside
      document.addEventListener('click', function(e) {
        if (!mobileMenu.contains(e.target) && !menuBtn.contains(e.target)) {
          mobileMenu.classList.remove('open');
        }
      });
    }
  });
  
  // Review slider functionality (multiple cards)
  document.addEventListener('DOMContentLoaded', function () {
    const reviewCards = Array.from(document.querySelectorAll('.review-card'));
    const prevBtn = document.querySelector('.review-arrow-prev');
    const nextBtn = document.querySelector('.review-arrow-next');
    let currentReview = 0;
    const visibleCount = 2; // Number of cards to show at once
  
    function showReviews(idx) {
      reviewCards.forEach((card, i) => {
        card.classList.remove('visible', 'left', 'right');
        if (i >= idx && i < idx + visibleCount) {
          card.classList.add('visible');
        } else if (i < idx) {
          card.classList.add('left');
        } else {
          card.classList.add('right');
        }
      });
      currentReview = idx;
    }
  
    function nextReview() {
      let nxt = currentReview + 1;
      if (nxt > reviewCards.length - visibleCount) {
        nxt = 0;
      }
      showReviews(nxt);
    }
  
    function prevReview() {
      let prev = currentReview - 1;
      if (prev < 0) {
        prev = reviewCards.length - visibleCount;
      }
      showReviews(prev);
    }
  
    if (prevBtn && nextBtn && reviewCards.length) {
      prevBtn.addEventListener('click', prevReview);
      nextBtn.addEventListener('click', nextReview);
      showReviews(0);
    }
  });
  document.addEventListener('DOMContentLoaded', function(){
    var cta = document.getElementById('cta');
    if(cta){
      cta.addEventListener('click', function(){
        var next = document.getElementById('next');
        if(next){
          next.scrollIntoView({behavior:'smooth',block:'start'});
        }
      });
    }
  
    /* Carousel behavior */
    var slides = Array.from(document.querySelectorAll('.slide'));
    var dots = Array.from(document.querySelectorAll('.dot'));
    var current = 0;
    var interval = 3000; // 3s
    var timer = null;
  
    function showSlide(index){
      if(!slides.length) return;
      slides.forEach(function(s,i){
        s.classList.toggle('active', i === index);
      });
      dots.forEach(function(d,i){
        d.classList.toggle('active', i === index);
      });
      current = index;
    }
  
    function nextSlide(){
      var nxt = (current + 1) % slides.length;
      showSlide(nxt);
    }
  
    // Dot click handlers
    dots.forEach(function(dot){
      dot.addEventListener('click', function(e){
        var idx = parseInt(dot.getAttribute('data-index'),10);
        showSlide(idx);
        resetTimer();
      });
    });
  
    function startTimer(){
      timer = setInterval(nextSlide, interval);
    }
    function resetTimer(){
      if(timer) clearInterval(timer);
      startTimer();
    }
  
    if(slides.length){
      showSlide(0);
      startTimer();
    }
  });
  
  // Card carousels for premium section
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.card-carousel').forEach(function(carousel) {
      const images = Array.from(carousel.querySelectorAll('.carousel-img'));
      const prevBtn = carousel.querySelector('.prev-btn');
      const nextBtn = carousel.querySelector('.next-btn');
      let current = 0;
  
      function showImage(idx) {
        images.forEach((img, i) => {
          img.classList.toggle('active', i === idx);
        });
        current = idx;
      }
      prevBtn.addEventListener('click', function() {
        showImage((current - 1 + images.length) % images.length);
      });
      nextBtn.addEventListener('click', function() {
        showImage((current + 1) % images.length);
      });
      showImage(0);
    });
  });
  
  // PARTNERS CAROUSEL (SEAMLESS INFINITE SCROLL)
  const partnerImages = [
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/557257/1.png',
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/557257/7.png',
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/557257/6.png',
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/557257/5.png',
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/557257/4.png',
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/557257/3.png',
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/557257/2.png',
  ];
  
  const partnersCarousel = document.getElementById('partners-carousel');
  
  function renderAllPartnerCards() {
    const allImages = [...partnerImages, ...partnerImages, ...partnerImages]; // duplicate for loop
    partnersCarousel.innerHTML = '';
  
    allImages.forEach(src => {
      const card = document.createElement('div');
      card.className = 'partner-card';
      const img = document.createElement('img');
      img.src = src;
      img.alt = 'Partner Logo';
      card.appendChild(img);
      partnersCarousel.appendChild(card);
    });
  }
  
  function startSmoothPartnersCarousel() {
    renderAllPartnerCards();
  
    const cardWidth = 240; // 200 (card) + ~40 padding (from CSS)
    const setWidth = partnerImages.length * cardWidth; // width of one full set
  
    let position = 0;
    const speed = 1; // smaller = slower
  
    function animate() {
      // move left continuously
      position += speed;
  
      // once we've moved one set width, jump back by exactly one set
      if (position >= setWidth) {
        position -= setWidth;
      }
  
      partnersCarousel.style.transform = `translateX(-${position}px)`;
      requestAnimationFrame(animate);
    }
  
    animate();
  }
  
  document.addEventListener('DOMContentLoaded', startSmoothPartnersCarousel);
  
  
  
  document.querySelector('.back-to-top').onclick = function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  
  // Animated Cursor Script
  const cursor = document.createElement('div');
  cursor.className = 'custom-cursor';
  const trail = document.createElement('div');
  trail.className = 'cursor-trail';
  document.body.append(cursor, trail);
  
  let mouseX = 0, mouseY = 0, trailX = 0, trailY = 0;
  document.addEventListener('mousemove', e => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    cursor.style.left = mouseX + 'px';
    cursor.style.top = mouseY + 'px';
  });
  function animateTrail() {
    trailX += (mouseX - trailX) * 0.18;
    trailY += (mouseY - trailY) * 0.18;
    trail.style.left = trailX + 'px';
    trail.style.top = trailY + 'px';
    requestAnimationFrame(animateTrail);
  }
  animateTrail();
  
  // Optional: Add .cursor-hover on hoverable elements
  ['a', 'button', '.cta', '.explore-btn'].forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
      el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
    });
  });