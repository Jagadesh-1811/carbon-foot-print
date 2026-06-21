// api.js - Core Javascript Logic for EcoTrace Frontend

const API_BASE = "http://localhost:8000/api";

// --- Auth System ---
async function login(email, password, fullName = null, isSignup = false) {
    try {
        const endpoint = isSignup ? `${API_BASE}/users/signup` : `${API_BASE}/users/login`;
        const bodyData = { email, password, fullName };

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData)
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Authentication failed');
        }
        localStorage.setItem('eco_user', data.uid);
        window.location.href = '/dashboard';
    } catch (err) {
        alert(err.message);
    }
}

function handleLoginClick() {
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');
    const nameInput = document.getElementById('signup-name');
    const signupFieldsVisible = !document.getElementById('signupFields').classList.contains('hidden');
    
    const email = emailInput ? emailInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value : '';
    const fullName = (signupFieldsVisible && nameInput) ? nameInput.value.trim() : null;
    
    if (!email) {
        alert('Please enter your email address');
        return;
    }
    
    login(email, password, fullName, signupFieldsVisible);
}

function logout() {
    localStorage.removeItem('eco_user');
    window.location.href = '/login';
}

function getUserId() {
    return localStorage.getItem('eco_user');
}

function checkAuth() {
    const publicPages = ['/', '/login', '/terms', '/support', '/services', '/privacy'];
    const isPublicPage = publicPages.includes(window.location.pathname);
    if (!getUserId() && !isPublicPage) {
        window.location.href = '/login';
    } else if (getUserId() && window.location.pathname === '/login') {
        window.location.href = '/dashboard';
    }
}

// --- API Wrappers ---
async function calculateCarbon(data) {
    const response = await fetch(`${API_BASE}/carbon/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.json();
}

async function saveCarbonResult(total_co2_kg_per_year, saved_kg) {
    const userId = getUserId();
    if (!userId) return null;
    try {
        const response = await fetch(`${API_BASE}/carbon/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, total_co2_kg_per_year, saved_kg })
        });
        return await response.json();
    } catch (err) {
        console.error('Error saving carbon footprint:', err);
        return null;
    }
}

async function fetchDashboard(userId) {
    if (!userId) return null;
    try {
        const response = await fetch(`${API_BASE}/carbon/dashboard/${userId}`);
        if (!response.ok) return null;
        return await response.json();
    } catch (err) {
        console.error('Error fetching dashboard:', err);
        return null;
    }
}

async function fetchGoals(userId) {
    if (!userId) return [];
    try {
        const response = await fetch(`${API_BASE}/goals/${userId}`);
        const data = await response.json();
        return data.goals || [];
    } catch (err) {
        console.error('Error fetching goals:', err);
        return [];
    }
}

async function createGoal(goalData) {
    const userId = getUserId();
    const response = await fetch(`${API_BASE}/goals/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...goalData, user_id: userId })
    });
    return response.json();
}

// --- Dynamic Profile Loader ---
async function loadUserProfile() {
    const userId = getUserId();
    if (!userId) return;
    
    try {
        const response = await fetch(`${API_BASE}/users/profile/${userId}`);
        if (!response.ok) return;
        const user = await response.json();
        
        // Update sidebar user card elements dynamically across all pages
        const sidebarCard = document.querySelector('nav .mt-auto, aside .mt-auto');
        if (sidebarCard) {
            const img = sidebarCard.querySelector('img');
            if (img) img.src = user.avatar_url;
            
            const textElements = Array.from(sidebarCard.querySelectorAll('p, span'))
                .filter(el => el.childNodes.length === 1 && el.childNodes[0].nodeType === Node.TEXT_NODE && el.textContent.trim().length > 0);
            
            if (textElements.length >= 2) {
                textElements[0].textContent = user.displayName;
                textElements[1].textContent = `LVL ${user.eco_level} ${user.eco_title}`;
            } else if (textElements.length === 1) {
                textElements[0].textContent = user.displayName;
            }
        }
        
        // If on the settings page, populate profile inputs with real data
        if (window.location.pathname === '/settings') {
            const sAvatar = document.getElementById('settings-avatar');
            const sName = document.getElementById('settings-name');
            const sRank = document.getElementById('settings-rank');
            const sImpact = document.getElementById('settings-impact-id');
            
            if (sAvatar) sAvatar.src = user.avatar_url;
            if (sName) sName.value = user.displayName;
            if (sRank) {
                const iconSpan = sRank.querySelector('span.material-symbols-outlined');
                sRank.innerHTML = '';
                if (iconSpan) sRank.appendChild(iconSpan);
                sRank.appendChild(document.createTextNode(` ${user.eco_title}`));
            }
            if (sImpact) sImpact.textContent = user.impact_id;
        }
    } catch (err) {
        console.error('Error loading user profile:', err);
    }
}

// --- Settings Profile Save ---
async function saveProfileChanges() {
    const userId = getUserId();
    if (!userId) return;
    
    const sName = document.getElementById('settings-name');
    const sAvatar = document.getElementById('settings-avatar');
    
    if (!sName || !sName.value.trim()) {
        alert('Please enter a display name');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/users/profile/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                displayName: sName.value.trim(),
                email: userId.includes('-') ? `${userId}@ecotrace.org` : `${userId}@ecotrace.org`,
                avatar_url: sAvatar ? sAvatar.src : null
            })
        });
        if (!response.ok) {
            throw new Error('Failed to update profile');
        }
        alert('Profile changes saved successfully! ✅');
        loadUserProfile();
    } catch (err) {
        alert('Error updating profile: ' + err.message);
    }
}

const AVATARS = [
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBTKipwUhnqDPmF0sg8cjq3Pt1GuNLxIewKESrdlF0otVZ-Upx1c28DDSCht2dbkhgQl-1KVFLOEIG1EUV_swxFj89a9VGDYGpkbwTsQVoI2lYdff0e6YaW8e5WNaK7BbyninFsx8DT9eGK-BHs8aeu_R-RPZHsTm7coJm8kDUSwdj035iHYw4-CSDXdnpWodVnQdWQWyy0kIshYWUltWhnTR-1Y85XO8FFAWQp1cMPE-OgaqZtD1Re_dWYBGukDTBN-0vwVNsZtGJO",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuAmbxBDuQgQ_juwISAMZ3VKBA0Ul3r4KzOGEnkY9NvCW3R-C-Yrc69icQvwjYdEPmqsP1oH69e35PqH_pl9wqZmeGyTEwtOMYQx_5yjAu2J7pid98PJcc_A9PjwSxhRH_0GBvsoGw89CFlTx0Q-b52Y-HcBHFL_mjyTP2vU-R0-WenWvVliiuq5g36wJZYSeFhEfg43-cOnmL0u-1inxvHwHiEEbRf5NeIuip7EjKMEQcRc0EwtA8zjnDXZKtGw-YGq32S_zLDZS71t",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBejfpGXvCCtMkYOxPMRyeDqGhVjJn8SBa44fQbXCNgUYrUCULqymkagAm_3T3U3UjXmBb4mt7zQEGGqEJJ62tGClN0TjfFoyRD9Ru_boDs-9GGVulKnCXHPdn_n1H1wMYVHK7aYUSLHskAt_920ea784ANfn0hmQviCEnbU6OPZ3qsPy08LmL3Cy_NKgQ_Zx7w-fboXgMuLRu8W_0ePzOtNw9i38jBqGoX1dOn1VLMG_EnScdl12ECrvnzui1ySr3vOI7U06YvkJhd",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuAuMr5CmBRj9f-hGfMzCTxl3HoCIpsB1xVJ35Nsb1ktU0hz7DRF8Cl4BmWlBi76usZUdkkoMVfJ5Pc_dbD_u4akQXxTUWRMjouZPieEQq_AZAJGBhSpQVB9ec8z7jY-7P5ATmP3--hGiSmI3QHEKFZHal7SYOXgFwqFTC7qSKqePrpyqeRmgv61ESqQ6-QzvqNE85JAGg013E5LqR9G4L9h-G9ht3slEU_kkbAo1kBRPhkYwNqnYudBDoXDFoQ6iylRSS2lfnwYKDbh"
];

function changeAvatar() {
    const sAvatar = document.getElementById('settings-avatar');
    if (!sAvatar) return;
    const currentSrc = sAvatar.src;
    let nextIndex = 0;
    const currentIndex = AVATARS.indexOf(currentSrc);
    if (currentIndex !== -1) {
        nextIndex = (currentIndex + 1) % AVATARS.length;
    } else {
        nextIndex = Math.floor(Math.random() * AVATARS.length);
    }
    sAvatar.src = AVATARS[nextIndex];
}

// --- Navigation Links setup ---
function setupNavigation() {
    const sidebarMap = {
        'dashboard': '/dashboard',
        'calculate': '/calculator',
        'track_changes': '/goals',
        'military_tech': '/rewards',
        'leaderboard': '#',
        'settings': '/settings',
        'logout': '#'
    };

    const links = document.querySelectorAll('nav a, nav button, aside a, aside button');
    links.forEach(link => {
        const iconSpan = link.querySelector('.material-symbols-outlined');
        if (iconSpan) {
            const iconText = iconSpan.textContent.trim();
            if (sidebarMap[iconText] && sidebarMap[iconText] !== '#') {
                if (link.tagName === 'A') {
                    link.href = sidebarMap[iconText];
                } else if (link.tagName === 'BUTTON') {
                    link.onclick = () => window.location.href = sidebarMap[iconText];
                }
            } else if (iconText === 'logout') {
                if (link.tagName === 'BUTTON') {
                    link.onclick = logout;
                } else {
                    link.href = '#';
                    link.onclick = (e) => { e.preventDefault(); logout(); };
                }
            }
        }
    });
}

// Run auth check immediately
checkAuth();

function updateHeaderLoginButtons() {
    const userId = getUserId();
    const loginBtn = document.getElementById('header-login-btn');
    if (loginBtn) {
        if (userId) {
            loginBtn.innerText = 'DASHBOARD';
            loginBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                window.location.href = '/dashboard';
            };
            
            // Add a logout button next to it if not already present
            let logoutBtn = document.getElementById('header-logout-btn');
            if (!logoutBtn) {
                logoutBtn = document.createElement('button');
                logoutBtn.id = 'header-logout-btn';
                logoutBtn.innerText = 'LOGOUT';
                
                // Style based on landing page header vs secondary page headers
                if (window.location.pathname === '/' || window.location.pathname === '/index.html' || window.location.pathname === '') {
                    logoutBtn.className = 'bg-white text-red-600 font-headline-md uppercase border-2 border-on-background py-2 px-6 neo-shadow hover:translate-x-1 hover:translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all active:translate-x-2 active:translate-y-2 active:shadow-none ml-2';
                } else {
                    logoutBtn.className = 'px-4 py-2 bg-white text-red-600 neo-border neo-shadow font-black uppercase text-xs hover:bg-red-100 transition-colors active:translate-x-1 active:translate-y-1 active:shadow-none ml-2';
                }
                logoutBtn.onclick = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    logout();
                };
                loginBtn.parentNode.insertBefore(logoutBtn, loginBtn.nextSibling);
            }
        } else {
            loginBtn.innerText = 'LOGIN';
            loginBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                window.location.href = '/login';
            };
            const logoutBtn = document.getElementById('header-logout-btn');
            if (logoutBtn) {
                logoutBtn.remove();
            }
        }
    }

    const heroCtaBtn = document.getElementById('hero-cta-btn');
    if (heroCtaBtn && userId) {
        heroCtaBtn.innerText = 'GO TO DASHBOARD';
        heroCtaBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            window.location.href = '/dashboard';
        };
    }

    const footerCtaBtn = document.getElementById('footer-cta-btn');
    if (footerCtaBtn && userId) {
        footerCtaBtn.innerText = 'GO TO DASHBOARD';
        footerCtaBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            window.location.href = '/dashboard';
        };
    }
}

async function firebaseGoogleLogin(idToken) {
    try {
        const response = await fetch(`${API_BASE}/users/google-login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Google authentication failed');
        }
        localStorage.setItem('eco_user', data.uid);
        window.location.href = '/dashboard';
    } catch (err) {
        alert(err.message);
    }
}

function handleGoogleLoginClick() {
    if (typeof openGoogleModal === 'function') {
        openGoogleModal();
    } else {
        login("google-warrior@ecotrace.network", "google-oauth-mock-pass", "Google Warrior");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    loadUserProfile();
    updateHeaderLoginButtons();
});

// --- Google Pay Integration ---
const baseRequest = {
  apiVersion: 2,
  apiVersionMinor: 0
};

const allowedCardNetworks = ["AMEX", "DISCOVER", "INTERAC", "JCB", "MASTERCARD", "VISA"];
const allowedCardAuthMethods = ["PAN_ONLY", "CRYPTOGRAM_3DS"];

const tokenizationSpecification = {
  type: 'PAYMENT_GATEWAY',
  parameters: {
    'gateway': 'example',
    'gatewayMerchantId': 'exampleGatewayMerchantId'
  }
};

const baseCardPaymentMethod = {
  type: 'CARD',
  parameters: {
    allowedAuthMethods: allowedCardAuthMethods,
    allowedCardNetworks: allowedCardNetworks
  }
};

const cardPaymentMethod = Object.assign(
  {},
  baseCardPaymentMethod,
  {
    tokenizationSpecification: tokenizationSpecification
  }
);

let paymentsClient = null;

function getGooglePaymentsClient() {
  if (paymentsClient === null) {
    paymentsClient = new google.payments.api.PaymentsClient({environment: 'TEST'});
  }
  return paymentsClient;
}

function getGoogleIsReadyToPayRequest() {
  return Object.assign(
    {},
    baseRequest,
    {
      allowedPaymentMethods: [baseCardPaymentMethod]
    }
  );
}

function initGooglePay(containerId, amountVal, labelVal, onSuccessCallback) {
  const paymentsClient = getGooglePaymentsClient();
  paymentsClient.isReadyToPay(getGoogleIsReadyToPayRequest())
    .then(function(response) {
      if (response.result) {
        const button = paymentsClient.createButton({
          buttonColor: 'black',
          buttonType: 'buy',
          onClick: () => onGooglePaymentButtonClicked(amountVal, labelVal, onSuccessCallback)
        });
        const container = document.getElementById(containerId);
        if (container) {
          container.innerHTML = '';
          container.appendChild(button);
        }
      }
    })
    .catch(function(err) {
      console.error("isReadyToPay error: ", err);
    });
}

function onGooglePaymentButtonClicked(amountVal, labelVal, onSuccessCallback) {
  const paymentDataRequest = getGooglePaymentDataRequest(amountVal, labelVal);
  const paymentsClient = getGooglePaymentsClient();
  paymentsClient.loadPaymentData(paymentDataRequest)
    .then(function(paymentData) {
      console.log("Payment Success", paymentData);
      if (onSuccessCallback) {
        onSuccessCallback(paymentData);
      } else {
        alert("Payment successful! Thank you for your support. ✅");
      }
    })
    .catch(function(err) {
      console.error("loadPaymentData error: ", err);
    });
}

function getGooglePaymentDataRequest(amountVal, labelVal) {
  const paymentDataRequest = Object.assign({}, baseRequest);
  paymentDataRequest.allowedPaymentMethods = [cardPaymentMethod];
  paymentDataRequest.transactionInfo = {
    displayItems: [{
      label: labelVal,
      type: 'LINE_ITEM',
      price: amountVal,
    }],
    totalPriceStatus: 'FINAL',
    totalPrice: amountVal,
    currencyCode: 'USD',
    countryCode: 'US'
  };
  paymentDataRequest.merchantInfo = {
    merchantName: 'EcoTrace Systems'
  };
  return paymentDataRequest;
}
