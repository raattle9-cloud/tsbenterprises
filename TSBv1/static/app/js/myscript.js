$(document).ready(function(){
    $('#slider1, #slider2, #slider3').owlCarousel({
        loop: true,
        margin: 20,
        responsiveClass: true,
        responsive: {
            0: {
                items: 2,
                nav: false,
                autoplay: true,
            },
            600: {
                items: 4,
                nav: true,
                autoplay: true,
            },
            1000: {
                items: 6,
                nav: true,
                loop: true,
                autoplay: true,
            }
        }
    });
});

$(document).ready(function() {
    $('.plus-cart').click(function(e){
        e.preventDefault();
        var id=$(this).attr("pid").toString();
        var btn = $(this);
        var quantityElement = $('#quantity-' + id);
        $.ajax({
            type:"GET",
            url:"/pluscart",
            data:{
                serv_id:id
            },
            success:function(data){
                if(quantityElement.length) {
                    var qtySpan = quantityElement[0];
                    if(qtySpan) {
                        qtySpan.textContent = data.quantity;
                    }
                }
                var amountEl = document.getElementById("amount");
                var totalEl = document.getElementById("totalamount");
                if(amountEl) amountEl.innerText = "₹" + parseFloat(data.amount).toFixed(2);
                if(totalEl) totalEl.innerText = "₹" + parseFloat(data.totalamount).toFixed(2);
                console.log("Button clicked and AJAX request successful", data);
            },
            error: function(xhr, status, error) {
                console.error("Error:", error);
                alert("Error updating cart. Please try again.");
            }
        })
    });

    $('.minus-cart').click(function(e){
    e.preventDefault();
    var id=$(this).attr("pid").toString();
    var btn = $(this);
    var quantityElement = $('#quantity-' + id);
    $.ajax({
        type:"GET",
        url:"/minuscart",
        data:{
            serv_id:id
        },
        success:function(data){
            if(data.quantity !== undefined) {
                if(quantityElement.length) {
                    if(data.quantity > 0) {
                        var qtySpan = quantityElement[0];
                        if(qtySpan) {
                            qtySpan.textContent = data.quantity;
                        }
                    } else {
                        // Item was removed, reload page
                        location.reload();
                        return;
                    }
                }
                var amountEl = document.getElementById("amount");
                var totalEl = document.getElementById("totalamount");
                if(amountEl) amountEl.innerText = "₹" + parseFloat(data.amount).toFixed(2);
                if(totalEl) totalEl.innerText = "₹" + parseFloat(data.totalamount).toFixed(2);
            } else {
                // Error response, reload page
                location.reload();
            }
        },
        error: function(xhr, status, error) {
            console.error("Error:", error);
            alert("Error updating cart. Please try again.");
        }
    })
    });

    $('.remove-cart').click(function(){
        var id=$(this).attr("pid").toString();
        var eml=this
        $.ajax({
            type:"GET",
            url:"/removecart",
            data:{
                prod_id:id
            },
            success:function(data){
                var amountEl = document.getElementById("amount");
                var totalEl = document.getElementById("totalamount");
                if(amountEl) amountEl.innerText = "₹" + parseFloat(data.amount).toFixed(2);
                if(totalEl) totalEl.innerText = "₹" + parseFloat(data.totalamount).toFixed(2);
                // remove the closest cart-item container (only this item)
                var cartItem = eml.closest('.cart-item');
                if (cartItem) { cartItem.remove(); }
            },
            error: function(xhr, status, error) {
                console.error("Error:", error);
                alert("Error removing item. Please try again.");
            }
        })
    });
});

$(document).ready(function() {
    $('.plus-wishlist').click(function(e){
        e.preventDefault();
        var id=$(this).attr("pid").toString();
        var btn = $(this);
        $.ajax({
            type:"GET",
            url:"/pluswishlist",
            data:{
                prod_id:id
            },
            success:function(data){
                // Only update if item was actually added (not if it was already in wishlist)
                if(data.added !== false) {
                    // Change button to minus-wishlist (remove from wishlist)
                    btn.removeClass('plus-wishlist btn-light').addClass('minus-wishlist btn-danger');
                    btn.find('i').removeClass('far').addClass('fas');
                    // Update wishlist count if badge exists (only wishlist badge, not cart badge)
                    // Target only wishlist badges, not cart badges
                    var wishlistBadges = $('.wishlist-btn .wishlist-count-badge');
                    if(wishlistBadges.length) {
                        // Get count from first badge only, ensure it's a valid number
                        var firstBadge = wishlistBadges.first();
                        var badgeText = firstBadge.text().trim();
                        // Extract only digits from the text
                        var badgeNumber = badgeText.match(/\d+/);
                        var currentCount = badgeNumber ? parseInt(badgeNumber[0]) : 0;
                        // Ensure it's a reasonable number (prevent huge numbers)
                        if(currentCount > 1000) currentCount = 0;
                        var newCount = currentCount + 1;
                        // Update all wishlist badges with the new count
                        wishlistBadges.text(newCount);
                    } else {
                        // If badge doesn't exist, create it
                        var wishlistBtns = $('.wishlist-btn');
                        wishlistBtns.each(function() {
                            if($(this).find('.wishlist-count-badge').length === 0) {
                                $(this).append('<span class="cart-badge-landing wishlist-count-badge">1</span>');
                            }
                        });
                    }
                }
            },
            error: function(xhr, status, error) {
                if(xhr.status === 401) {
                    alert("Please login to add items to your wishlist.");
                    window.location.href = "/accounts/login/";
                } else {
                    alert("Error adding to wishlist. Please try again.");
                }
            }
        })
    });

    $('.minus-wishlist').click(function(e){
        e.preventDefault();
        var id=$(this).attr("pid").toString();
        var btn = $(this);
        $.ajax({
            type:"GET",
            url:"/minuswishlist",
            data:{
                prod_id:id
            },
            success:function(data){
                // Check if we're on the wishlist page - if so, remove the entire card
                if(window.location.pathname.includes('wishlist')) {
                    // Find the parent column div that contains the card
                    var wishlistCard = btn.closest('.col-md-6, .col-lg-4');
                    if(!wishlistCard.length) {
                        wishlistCard = btn.closest('.card').parent();
                    }
                    if(wishlistCard.length) {
                        wishlistCard.fadeOut(300, function() {
                            $(this).remove();
                            // Check if any wishlist items remain by looking for cards with minus-wishlist buttons
                            var remainingItems = $('.minus-wishlist').length;
                            if(remainingItems === 0) {
                                // No items left, reload to show empty state
                                setTimeout(function() {
                                    location.reload();
                                }, 100);
                            }
                        });
                    }
                } else {
                    // On services page or detail page - change button to plus-wishlist
                    btn.removeClass('minus-wishlist btn-danger').addClass('plus-wishlist btn-light');
                    btn.find('i').removeClass('fas').addClass('far');
                }
                
                // Update wishlist count if badge exists (only wishlist badge, not cart badge)
                // Target only wishlist badges, not cart badges
                var wishlistBadges = $('.wishlist-btn .wishlist-count-badge');
                if(wishlistBadges.length) {
                    // Get count from first badge only, ensure it's a valid number
                    var firstBadge = wishlistBadges.first();
                    var badgeText = firstBadge.text().trim();
                    // Extract only digits from the text
                    var badgeNumber = badgeText.match(/\d+/);
                    var currentCount = badgeNumber ? parseInt(badgeNumber[0]) : 0;
                    // Ensure it's a reasonable number (prevent huge numbers)
                    if(currentCount > 1000) currentCount = 0;
                    if(currentCount > 0) {
                        var newCount = currentCount - 1;
                        if(newCount > 0) {
                            // Update all wishlist badges with the new count
                            wishlistBadges.text(newCount);
                        } else {
                            // Remove badge if count reaches 0
                            wishlistBadges.remove();
                        }
                    }
                }
            },
            error: function(xhr, status, error) {
                if(xhr.status === 401) {
                    alert("Please login to manage your wishlist.");
                    window.location.href = "/accounts/login/";
                } else {
                    alert("Error removing from wishlist. Please try again.");
                }
            }
        })
    });
});

 // Back to top button
 $(window).scroll(function () {
    if ($(this).scrollTop() > 300) {
        $('.back-to-top').fadeIn('slow');
    } else {
        $('.back-to-top').fadeOut('slow');
    }
});
$('.back-to-top').click(function () {
    $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
    return false;
});
