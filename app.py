from flask import Flask, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import platform
import socket
import shutil
import subprocess
import psutil
import ipaddress
from datetime import datetime

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY"
)

DATABASE = "void_intel.db"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():

    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if admin_email and admin_password:

        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (admin_email,)
        ).fetchone()

        if not existing:

            hashed_password = generate_password_hash(
                admin_password
            )

            connection.execute("""
                INSERT INTO users
                (username, email, password, is_admin, created_at)
                VALUES (?, ?, ?, 1, ?)
            """, (
                "VOID_ADMIN",
                admin_email,
                hashed_password,
                datetime.utcnow().isoformat()
            ))

            connection.commit()

    connection.close()


init_database()


# ============================================================
# COUNTRY DATABASE
# ============================================================

COUNTRIES = [

    {
        "name": "Netherlands",
        "code": "NL",
        "capital": "Amsterdam",
        "region": "Europe",
        "currency": "Euro",
        "language": "Dutch"
    },

    {
        "name": "Belgium",
        "code": "BE",
        "capital": "Brussels",
        "region": "Europe",
        "currency": "Euro",
        "language": "Dutch, French, German"
    },

    {
        "name": "Germany",
        "code": "DE",
        "capital": "Berlin",
        "region": "Europe",
        "currency": "Euro",
        "language": "German"
    },

    {
        "name": "France",
        "code": "FR",
        "capital": "Paris",
        "region": "Europe",
        "currency": "Euro",
        "language": "French"
    },

    {
        "name": "Spain",
        "code": "ES",
        "capital": "Madrid",
        "region": "Europe",
        "currency": "Euro",
        "language": "Spanish"
    },

    {
        "name": "Italy",
        "code": "IT",
        "capital": "Rome",
        "region": "Europe",
        "currency": "Euro",
        "language": "Italian"
    },

    {
        "name": "Portugal",
        "code": "PT",
        "capital": "Lisbon",
        "region": "Europe",
        "currency": "Euro",
        "language": "Portuguese"
    },

    {
        "name": "United Kingdom",
        "code": "GB",
        "capital": "London",
        "region": "Europe",
        "currency": "Pound Sterling",
        "language": "English"
    },

    {
        "name": "Ireland",
        "code": "IE",
        "capital": "Dublin",
        "region": "Europe",
        "currency": "Euro",
        "language": "English, Irish"
    },

    {
        "name": "Switzerland",
        "code": "CH",
        "capital": "Bern",
        "region": "Europe",
        "currency": "Swiss Franc",
        "language": "German, French, Italian, Romansh"
    },

    {
        "name": "United States",
        "code": "US",
        "capital": "Washington, D.C.",
        "region": "North America",
        "currency": "US Dollar",
        "language": "English"
    },

    {
        "name": "Canada",
        "code": "CA",
        "capital": "Ottawa",
        "region": "North America",
        "currency": "Canadian Dollar",
        "language": "English, French"
    },

    {
        "name": "Mexico",
        "code": "MX",
        "capital": "Mexico City",
        "region": "North America",
        "currency": "Mexican Peso",
        "language": "Spanish"
    },

    {
        "name": "Brazil",
        "code": "BR",
        "capital": "Brasilia",
        "region": "South America",
        "currency": "Brazilian Real",
        "language": "Portuguese"
    },

    {
        "name": "Argentina",
        "code": "AR",
        "capital": "Buenos Aires",
        "region": "South America",
        "currency": "Argentine Peso",
        "language": "Spanish"
    },

    {
        "name": "Nigeria",
        "code": "NG",
        "capital": "Abuja",
        "region": "Africa",
        "currency": "Naira",
        "language": "English"
    },

    {
        "name": "South Africa",
        "code": "ZA",
        "capital": "Pretoria",
        "region": "Africa",
        "currency": "South African Rand",
        "language": "Multiple"
    },

    {
        "name": "Egypt",
        "code": "EG",
        "capital": "Cairo",
        "region": "Africa",
        "currency": "Egyptian Pound",
        "language": "Arabic"
    },

    {
        "name": "Kenya",
        "code": "KE",
        "capital": "Nairobi",
        "region": "Africa",
        "currency": "Kenyan Shilling",
        "language": "English, Swahili"
    },

    {
        "name": "India",
        "code": "IN",
        "capital": "New Delhi",
        "region": "Asia",
        "currency": "Indian Rupee",
        "language": "Hindi, English"
    },

    {
        "name": "China",
        "code": "CN",
        "capital": "Beijing",
        "region": "Asia",
        "currency": "Yuan",
        "language": "Chinese"
    },

    {
        "name": "Japan",
        "code": "JP",
        "capital": "Tokyo",
        "region": "Asia",
        "currency": "Yen",
        "language": "Japanese"
    },

    {
        "name": "South Korea",
        "code": "KR",
        "capital": "Seoul",
        "region": "Asia",
        "currency": "Won",
        "language": "Korean"
    },

    {
        "name": "Australia",
        "code": "AU",
        "capital": "Canberra",
        "region": "Oceania",
        "currency": "Australian Dollar",
        "language": "English"
    },

    {
        "name": "New Zealand",
        "code": "NZ",
        "capital": "Wellington",
        "region": "Oceania",
        "currency": "New Zealand Dollar",
        "language": "English, Maori"
    }
]


# ============================================================
# HTML / CSS / JAVASCRIPT
# ============================================================

HTML = r"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>VOID INTEL-V2</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    scroll-behavior: smooth;
}

body {
    background: #050608;
    color: #eeeeee;
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.6;
}

header {
    position: fixed;
    top: 0;
    left: 0;

    width: 100%;
    height: 70px;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 6%;

    background: rgba(5, 6, 8, 0.97);

    border-bottom: 1px solid #22262c;

    z-index: 1000;
}

.logo {
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 2px;
}

.logo span {
    color: #7dff00;
}

nav {
    display: flex;
    gap: 18px;
}

nav a {
    color: #aaa;
    text-decoration: none;
    font-size: 14px;
}

nav a:hover {
    color: #7dff00;
}

button {
    cursor: pointer;
    font-weight: bold;
}

.login-button {
    background: #7dff00;
    color: #050608;
    border: none;
    border-radius: 5px;
    padding: 10px 18px;
}

.hero {
    min-height: 100vh;

    display: flex;
    align-items: center;

    padding: 120px 8%;

    background:
        radial-gradient(
            circle at center,
            #182500,
            #050608 55%
        );
}

.hero-content {
    max-width: 900px;
}

.tag {
    color: #7dff00;
    letter-spacing: 4px;
    font-size: 12px;
    margin-bottom: 20px;
}

h1 {
    font-size: clamp(55px, 10vw, 125px);
    line-height: .95;
    letter-spacing: -5px;
}

h1 span {
    color: #7dff00;
}

.hero-text {
    color: #999;
    font-size: 18px;
    max-width: 700px;
    margin: 30px 0;
}

.hero-buttons {
    display: flex;
    gap: 15px;
}

.primary {
    background: #7dff00;
    color: #050608;
    border: none;
    border-radius: 5px;
    padding: 14px 22px;
}

.secondary {
    background: transparent;
    color: white;
    border: 1px solid #444;
    border-radius: 5px;
    padding: 14px 22px;
}

section {
    padding: 110px 8%;
    border-top: 1px solid #1c2025;
}

.section-label {
    color: #7dff00;
    font-size: 12px;
    letter-spacing: 3px;
}

.section-title {
    font-size: 42px;
    margin-top: 5px;
    margin-bottom: 35px;
}

.search-area {
    max-width: 850px;
    display: flex;
}

.search-area input {
    flex: 1;
    margin: 0;
    border-radius: 5px 0 0 5px;
}

.search-area button {
    width: 140px;
    background: #7dff00;
    border: none;
    border-radius: 0 5px 5px 0;
}

input {
    width: 100%;
    background: #0d1014;
    color: white;
    border: 1px solid #292e35;
    border-radius: 5px;
    padding: 14px;
    margin-bottom: 12px;
    outline: none;
}

input:focus {
    border-color: #7dff00;
}

.result {
    max-width: 950px;
    margin-top: 25px;
    padding: 25px;
    background: #0b0e12;
    border: 1px solid #242931;
    border-radius: 8px;
    color: #aaa;
    overflow-wrap: break-word;
}

.cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}

.card {
    background: #0b0e12;
    border: 1px solid #242931;
    border-radius: 8px;
    padding: 30px;
}

.card h3 {
    margin-bottom: 10px;
}

.card p {
    color: #888;
    margin-bottom: 20px;
}

.card button {
    background: #7dff00;
    border: none;
    padding: 10px 15px;
}

.country-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
}

.country-card {
    background: #0b0e12;
    border: 1px solid #242931;
    border-radius: 8px;
    padding: 20px;
}

.country-card h3 {
    color: #7dff00;
    margin-bottom: 10px;
}

.country-card p {
    color: #999;
    font-size: 14px;
}

.about {
    max-width: 1000px;
}

.about-text {
    color: #999;
    max-width: 750px;
}

footer {
    padding: 40px 8%;
    border-top: 1px solid #22262c;
    color: #666;
}

footer strong {
    color: #7dff00;
}

.modal {
    display: none;

    position: fixed;
    inset: 0;

    background: rgba(0, 0, 0, .88);

    align-items: center;
    justify-content: center;

    z-index: 2000;

    overflow-y: auto;
}

.modal-box {
    width: 90%;
    max-width: 450px;

    background: #0b0e12;

    border: 1px solid #343a42;

    border-radius: 10px;

    padding: 35px;

    position: relative;

    margin: 30px auto;
}

.modal-box h2 {
    margin-bottom: 20px;
}

.close {
    position: absolute;

    right: 15px;
    top: 10px;

    background: none;
    border: none;

    color: #aaa;

    font-size: 28px;
}

.close:hover {
    color: white;
}

.full {
    width: 100%;
}

.message {
    color: #7dff00;
    min-height: 20px;
    margin-top: 8px;
}

.error {
    color: #ff6060;
}

hr {
    border: none;
    border-top: 1px solid #292e35;
    margin: 25px 0;
}

pre {
    white-space: pre-wrap;
    color: #888;
    margin-top: 15px;
}

.admin-panel {
    display: none;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

th,
td {
    border-bottom: 1px solid #292e35;
    padding: 12px;
    text-align: left;
}

th {
    color: #7dff00;
}

td {
    color: #aaa;
}

@media(max-width: 900px) {

    nav {
        display: none;
    }

    .cards {
        grid-template-columns: 1fr;
    }

    .country-grid {
        grid-template-columns: 1fr;
    }

    .search-area {
        flex-direction: column;
    }

    .search-area input {
        border-radius: 5px;
        margin-bottom: 10px;
    }

    .search-area button {
        width: 100%;
        border-radius: 5px;
        padding: 14px;
    }

    h1 {
        font-size: 60px;
    }

    .hero-buttons {
        flex-direction: column;
    }

}

</style>

</head>


<body>


<header>

    <div class="logo">
        <span>VOID</span> INTEL-V2
    </div>

    <nav>

        <a href="#home">Home</a>

        <a href="#intel">Intel</a>

        <a href="#countries">Countries</a>

        <a href="#system">System</a>

        <a href="#about">About</a>

    </nav>

    <button
        class="login-button"
        onclick="openLogin()">

        Login

    </button>

</header>


<main>


<!-- ======================================================
     HOME
======================================================= -->

<section id="home" class="hero">

    <div class="hero-content">

        <div class="tag">
            INTELLIGENCE • DIAGNOSTICS • ANALYSIS
        </div>

        <h1>
            VOID
            <span>INTEL-V2</span>
        </h1>

        <p class="hero-text">

            A modern intelligence and diagnostic
            dashboard for authorized network,
            country and system analysis.

        </p>

        <div class="hero-buttons">

            <button
                class="primary"
                onclick="openLogin()">

                ACCESS VOID INTEL

            </button>

            <button
                class="secondary"
                onclick="goTo('intel')">

                START SEARCH

            </button>

        </div>

    </div>

</section>


<!-- ======================================================
     IP INTELLIGENCE
======================================================= -->

<section id="intel">

    <div class="section-label">
        INTELLIGENCE SEARCH
    </div>

    <h2 class="section-title">
        IP Intelligence
    </h2>

    <div class="search-area">

        <input
            id="ipInput"
            type="text"
            placeholder="Enter an IP address">

        <button onclick="lookupIP()">
            SEARCH
        </button>

    </div>

    <div
        id="ipResult"
        class="result">

        Enter an IP address to begin.

    </div>

</section>


<!-- ======================================================
     COUNTRIES
======================================================= -->

<section id="countries">

    <div class="section-label">
        GLOBAL INTELLIGENCE
    </div>

    <h2 class="section-title">
        Countries
    </h2>

    <div class="search-area">

        <input
            id="countryInput"
            type="text"
            placeholder="Search country or country code">

        <button onclick="searchCountries()">
            SEARCH
        </button>

    </div>

    <div
        id="countryResult"
        class="result">

        Search for a country or leave the
        box empty to show all available countries.

    </div>

</section>


<!-- ======================================================
     SYSTEM
======================================================= -->

<section id="system">

    <div class="section-label">
        DEVICE ANALYSIS
    </div>

    <h2 class="section-title">
        System Diagnostics
    </h2>


    <div class="cards">


        <div class="card">

            <h3>
                PC HEALTH
            </h3>

            <p>
                Check CPU, memory, disk and
                operating-system information.
            </p>

            <button onclick="systemCheck()">
                RUN CHECK
            </button>

        </div>


        <div class="card">

            <h3>
                FIREWALL
            </h3>

            <p>
                Check the firewall status of
                the server machine.
            </p>

            <button onclick="firewallCheck()">
                CHECK FIREWALL
            </button>

        </div>


        <div class="card">

            <h3>
                VOID AI
            </h3>

            <p>
                Get explanations about the
                diagnostic information.
            </p>

            <button onclick="openAI()">
                OPEN AI
            </button>

        </div>


    </div>


    <div
        id="systemResult"
        class="result">

        System results will appear here.

    </div>

</section>


<!-- ======================================================
     ADMIN
======================================================= -->

<section
    id="adminSection"
    class="admin-panel">

    <div class="section-label">
        ADMINISTRATION
    </div>

    <h2 class="section-title">
        VOID INTEL ADMIN
    </h2>

    <button
        class="primary"
        onclick="loadAdminUsers()">

        LOAD USERS

    </button>

    <div
        id="adminResult"
        class="result">

        Administrator controls are ready.

    </div>

</section>


<!-- ======================================================
     ABOUT
======================================================= -->

<section id="about" class="about">

    <div class="section-label">
        ABOUT
    </div>

    <h2 class="section-title">
        VOID INTEL-V2
    </h2>

    <p class="about-text">

        VOID INTEL-V2 is a diagnostic and
        intelligence dashboard for authorized
        security and system analysis.

        Use the system only on computers,
        networks and IP information that you
        own or are authorized to inspect.

    </p>

</section>


</main>


<footer>

    <strong>
        VOID INTEL-V2
    </strong>

    <br>

    Authorized diagnostic use only.

</footer>


<!-- ======================================================
     LOGIN MODAL
======================================================= -->

<div
    id="loginModal"
    class="modal">

    <div class="modal-box">

        <button
            class="close"
            onclick="closeLogin()">

            ×

        </button>

        <h2>
            VOID INTEL LOGIN
        </h2>


        <input
            id="loginEmail"
            type="email"
            placeholder="Email">


        <input
            id="loginPassword"
            type="password"
            placeholder="Password">


        <button
            class="primary full"
            onclick="login()">

            LOGIN

        </button>


        <div
            id="loginMessage"
            class="message">
        </div>


        <hr>


        <h3>
            CREATE ACCOUNT
        </h3>


        <input
            id="registerUsername"
            type="text"
            placeholder="Username">


        <input
            id="registerEmail"
            type="email"
            placeholder="Email">


        <input
            id="registerPassword"
            type="password"
            placeholder="Password">


        <button
            class="secondary full"
            onclick="register()">

            SIGN UP

        </button>


        <div
            id="registerMessage"
            class="message">
        </div>

    </div>

</div>


<!-- ======================================================
     AI MODAL
======================================================= -->

<div
    id="aiModal"
    class="modal">

    <div class="modal-box">

        <button
            class="close"
            onclick="closeAI()">

            ×

        </button>

        <h2>
            VOID AI
        </h2>

        <p>
            Ask about the diagnostic information.
        </p>

        <br>

        <input
            id="aiQuestion"
            type="text"
            placeholder="Ask a question">

        <button
            class="primary full"
            onclick="askAI()">

            ASK VOID AI

        </button>

        <div
            id="aiAnswer"
            class="message">

        </div>

    </div>

</div>


<script>


// ======================================================
// NAVIGATION
// ======================================================

function goTo(id) {

    const element =
        document.getElementById(id);

    if (element) {

        element.scrollIntoView({
            behavior: "smooth"
        });

    }

}


// ======================================================
// LOGIN
// ======================================================

function openLogin() {

    document.getElementById(
        "loginModal"
    ).style.display = "flex";

}


function closeLogin() {

    document.getElementById(
        "loginModal"
    ).style.display = "none";

}


// ======================================================
// REGISTER
// ======================================================

async function register() {

    const username =
        document.getElementById(
            "registerUsername"
        ).value.trim();

    const email =
        document.getElementById(
            "registerEmail"
        ).value.trim();

    const password =
        document.getElementById(
            "registerPassword"
        ).value;

    const message =
        document.getElementById(
            "registerMessage"
        );


    if (!username || !email || !password) {

        message.textContent =
            "Please fill in all fields.";

        return;

    }


    if (!email.includes("@")) {

        message.textContent =
            "Email must contain @.";

        return;

    }


    if (password.length < 8) {

        message.textContent =
            "Password must contain at least 8 characters.";

        return;

    }


    try {

        const response =
            await fetch(
                "/register",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        username,
                        email,
                        password
                    })
                }
            );


        const data =
            await response.json();


        message.textContent =
            data.message;


        if (data.success) {

            document.getElementById(
                "registerUsername"
            ).value = "";

            document.getElementById(
                "registerEmail"
            ).value = "";

            document.getElementById(
                "registerPassword"
            ).value = "";

        }


    } catch (error) {

        message.textContent =
            "Server connection failed.";

    }

}


// ======================================================
// LOGIN
// ======================================================

async function login() {

    const email =
        document.getElementById(
            "loginEmail"
        ).value.trim();

    const password =
        document.getElementById(
            "loginPassword"
        ).value;

    const message =
        document.getElementById(
            "loginMessage"
        );


    if (!email || !password) {

        message.textContent =
            "Enter your email and password.";

        return;

    }


    try {

        const response =
            await fetch(
                "/login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        email,
                        password
                    })
                }
            );


        const data =
            await response.json();


        message.textContent =
            data.message;


        if (data.success) {

            setTimeout(
                function() {

                    closeLogin();

                    if (data.admin) {

                        alert(
                            "Administrator login successful."
                        );

                        document.getElementById(
                            "adminSection"
                        ).style.display = "block";

                        goTo("adminSection");

                    } else {

                        alert(
                            "Welcome to VOID INTEL-V2."
                        );

                    }

                },
                500
            );

        }


    } catch (error) {

        message.textContent =
            "Unable to connect to VOID INTEL.";

    }

}


// ======================================================
// IP INTELLIGENCE
// ======================================================

async function lookupIP() {

    const ip =
        document.getElementById(
            "ipInput"
        ).value.trim();

    const result =
        document.getElementById(
            "ipResult"
        );


    if (!ip) {

        result.textContent =
            "Please enter an IP address.";

        return;

    }


    result.textContent =
        "Checking IP...";


    try {

        const response =
            await fetch(
                "/api/ip?ip=" +
                encodeURIComponent(ip)
            );


        const data =
            await response.json();


        if (!data.success) {

            result.textContent =
                data.message;

            return;

        }


        let countryHTML = "";


        if (data.country) {

            countryHTML =

                "<p><strong>Country:</strong> " +
                escapeHTML(
                    data.country.name
                ) +
                "</p>" +

                "<p><strong>Country Code:</strong> " +
                escapeHTML(
                    data.country.code
                ) +
                "</p>" +

                "<p><strong>Capital:</strong> " +
                escapeHTML(
                    data.country.capital
                ) +
                "</p>" +

                "<p><strong>Region:</strong> " +
                escapeHTML(
                    data.country.region
                ) +
                "</p>";

        }


        result.innerHTML =

            "<h3>IP INTELLIGENCE</h3>" +

            "<br>" +

            "<p><strong>IP:</strong> " +
            escapeHTML(data.ip) +
            "</p>" +

            "<p><strong>Type:</strong> " +
            escapeHTML(data.type) +
            "</p>" +

            "<p><strong>Status:</strong> " +
            escapeHTML(data.status) +
            "</p>" +

            countryHTML +

            "<br>" +

            "<p>" +
            escapeHTML(data.note) +
            "</p>";

    }


    catch (error) {

        result.textContent =
            "IP search failed.";

    }

}


// ======================================================
// COUNTRIES
// ======================================================

async function searchCountries() {

    const search =
        document.getElementById(
            "countryInput"
        ).value.trim();


    const result =
        document.getElementById(
            "countryResult"
        );


    result.textContent =
        "Searching countries...";


    try {

        const response =
            await fetch(
                "/api/countries?search=" +
                encodeURIComponent(search)
            );


        const data =
            await response.json();


        if (!data.success ||
            data.countries.length === 0) {

            result.textContent =
                "No country found.";

            return;

        }


        let html =
            "<h3>COUNTRY RESULTS</h3><br>" +

            "<div class='country-grid'>";


        data.countries.forEach(
            function(country) {

                html +=

                    "<div class='country-card'>" +

                    "<h3>" +
                    escapeHTML(country.name) +
                    "</h3>" +

                    "<p><strong>Code:</strong> " +
                    escapeHTML(country.code) +
                    "</p>" +

                    "<p><strong>Capital:</strong> " +
                    escapeHTML(country.capital) +
                    "</p>" +

                    "<p><strong>Region:</strong> " +
                    escapeHTML(country.region) +
                    "</p>" +

                    "<p><strong>Currency:</strong> " +
                    escapeHTML(country.currency) +
                    "</p>" +

                    "<p><strong>Language:</strong> " +
                    escapeHTML(country.language) +
                    "</p>" +

                    "</div>";

            }
        );


        html += "</div>";


        result.innerHTML =
            html;

    }


    catch (error) {

        result.textContent =
            "Country search failed.";

    }

}


// ======================================================
// SYSTEM CHECK
// ======================================================

async function systemCheck() {

    const result =
        document.getElementById(
            "systemResult"
        );


    result.textContent =
        "Running system diagnostics...";


    try {

        const response =
            await fetch(
                "/api/system"
            );


        const data =
            await response.json();


        if (!data.success) {

            result.textContent =
                data.message;

            return;

        }


        result.innerHTML =

            "<h3>SYSTEM REPORT</h3><br>" +

            "<p><strong>Operating System:</strong> " +
            escapeHTML(data.system) +
            "</p>" +

            "<p><strong>Version:</strong> " +
            escapeHTML(data.release) +
            "</p>" +

            "<p><strong>Machine:</strong> " +
            escapeHTML(data.machine) +
            "</p>" +

            "<p><strong>CPU Usage:</strong> " +
            escapeHTML(data.cpu_percent) +
            "%</p>" +

            "<p><strong>Memory Usage:</strong> " +
            escapeHTML(data.memory_percent) +
            "%</p>" +

            "<p><strong>Memory Total:</strong> " +
            escapeHTML(data.memory_total_gb) +
            " GB</p>" +

            "<p><strong>Memory Used:</strong> " +
            escapeHTML(data.memory_used_gb) +
            " GB</p>" +

            "<p><strong>Disk Total:</strong> " +
            escapeHTML(data.disk_total_gb) +
            " GB</p>" +

            "<p><strong>Disk Used:</strong> " +
            escapeHTML(data.disk_used_gb) +
            " GB</p>" +

            "<p><strong>Disk Free:</strong> " +
            escapeHTML(data.disk_free_gb) +
            " GB</p>";

    }


    catch (error) {

        result.textContent =
            "System check failed.";

    }

}


// ======================================================
// FIREWALL
// ======================================================

async function firewallCheck() {

    const result =
        document.getElementById(
            "systemResult"
        );


    result.textContent =
        "Checking firewall...";


    try {

        const response =
            await fetch(
                "/api/firewall"
            );


        const data =
            await response.json();


        if (!data.success) {

            result.textContent =
                data.message;

            return;

        }


        result.innerHTML =

            "<h3>FIREWALL REPORT</h3><br>" +

            "<p><strong>Platform:</strong> " +
            escapeHTML(data.platform) +
            "</p>" +

            "<p><strong>Status:</strong> " +
            escapeHTML(data.firewall) +
            "</p>" +

            "<pre>" +
            escapeHTML(
                data.details || ""
            ) +
            "</pre>";

    }


    catch (error) {

        result.textContent =
            "Firewall check failed.";

    }

}


// ======================================================
// VOID AI
// ======================================================

function openAI() {

    document.getElementById(
        "aiModal"
    ).style.display = "flex";

}


function closeAI() {

    document.getElementById(
        "aiModal"
    ).style.display = "none";

}


function askAI() {

    const question =
        document.getElementById(
            "aiQuestion"
        ).value.trim();


    const answer =
        document.getElementById(
            "aiAnswer"
        );


    if (!question) {

        answer.textContent =
            "Enter a question first.";

        return;

    }


    answer.textContent =

        "VOID AI: I can explain the diagnostic " +
        "information displayed by VOID INTEL-V2. " +
        "A real AI service can be connected to " +
        "this section later.";

}


// ======================================================
// ADMIN USERS
// ======================================================

async function loadAdminUsers() {

    const result =
        document.getElementById(
            "adminResult"
        );


    result.textContent =
        "Loading users...";


    try {

        const response =
            await fetch(
                "/api/admin/users"
            );


        const data =
            await response.json();


        if (!data.success) {

            result.textContent =
                data.message;

            return;

        }


        let html =

            "<h3>REGISTERED USERS</h3>" +

            "<table>" +

            "<tr>" +

            "<th>ID</th>" +

            "<th>Username</th>" +

            "<th>Email</th>" +

            "<th>Admin</th>" +

            "<th>Created</th>" +

            "</tr>";


        data.users.forEach(
            function(user) {

                html +=

                    "<tr>" +

                    "<td>" +
                    escapeHTML(user.id) +
                    "</td>" +

                    "<td>" +
                    escapeHTML(user.username) +
                    "</td>" +

                    "<td>" +
                    escapeHTML(user.email) +
                    "</td>" +

                    "<td>" +
                    (
                        user.is_admin
                        ? "YES"
                        : "NO"
                    ) +
                    "</td>" +

                    "<td>" +
                    escapeHTML(user.created_at) +
                    "</td>" +

                    "</tr>";

            }
        );


        html += "</table>";


        result.innerHTML =
            html;

    }


    catch (error) {

        result.textContent =
            "Unable to load admin data.";

    }

}


// ======================================================
// HTML SECURITY
// ======================================================

function escapeHTML(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}


// ======================================================
// CLOSE MODALS
// ======================================================

window.addEventListener(
    "click",
    function(event) {

        const loginModal =
            document.getElementById(
                "loginModal"
            );

        const aiModal =
            document.getElementById(
                "aiModal"
            );


        if (event.target === loginModal) {

            closeLogin();

        }


        if (event.target === aiModal) {

            closeAI();

        }

    }
);


</script>


</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return HTML


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/healthz")
def healthz():

    return jsonify({

        "status": "online",

        "application":
            "VOID INTEL-V2"

    }), 200


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["POST"]
)
def register():

    data =
        request.get_json(
            silent=True
        ) or {}


    username =
        data.get(
            "username",
            ""
        ).strip()


    email =
        data.get(
            "email",
            ""
        ).strip()


    password =
        data.get(
            "password",
            ""
        )


    if not username or not email or not password:

        return jsonify({

            "success": False,

            "message":
                "All fields are required."

        }), 400


    if "@" not in email:

        return jsonify({

            "success": False,

            "message":
                "Email must contain @."

        }), 400


    if len(password) < 8:

        return jsonify({

            "success": False,

            "message":
                "Password must contain at least 8 characters."

        }), 400


    connection =
        get_db()


    existing =
        connection.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            OR email = ?
            """,
            (
                username,
                email
            )
        ).fetchone()


    if existing:

        connection.close()


        return jsonify({

            "success": False,

            "message":
                "Username or email already exists."

        }), 409


    hashed_password =
        generate_password_hash(
            password
        )


    connection.execute(
        """
        INSERT INTO users
        (username, email, password, is_admin, created_at)
        VALUES (?, ?, ?, 0, ?)
        """,
        (
            username,
            email,
            hashed_password,
            datetime.utcnow().isoformat()
        )
    )


    connection.commit()

    connection.close()


    return jsonify({

        "success": True,

        "message":
            "Account created successfully."

    })


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    data =
        request.get_json(
            silent=True
        ) or {}


    email =
        data.get(
            "email",
            ""
        ).strip()


    password =
        data.get(
            "password",
            ""
        )


    connection =
        get_db()


    user =
        connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()


    connection.close()


    if not user:

        return jsonify({

            "success": False,

            "message":
                "Invalid email or password."

        }), 401


    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({

            "success": False,

            "message":
                "Invalid email or password."

        }), 401


    session["user_id"] =
        user["id"]


    session["username"] =
        user["username"]


    session["is_admin"] =
        bool(user["is_admin"])


    return jsonify({

        "success": True,

        "message":
            "Login successful.",

        "admin":
            bool(user["is_admin"])

    })


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# CURRENT USER
# ============================================================

@app.route("/api/me")
def current_user():

    if "user_id" not in session:

        return jsonify({

            "logged_in": False

        })


    return jsonify({

        "logged_in": True,

        "username":
            session.get(
                "username"
            ),

        "admin":
            session.get(
                "is_admin",
                False
            )

    })


# ============================================================
# IP INTELLIGENCE
# ============================================================

@app.route("/api/ip")
def ip_lookup():

    ip =
        request.args.get(
            "ip",
            ""
        ).strip()


    if not ip:

        return jsonify({

            "success": False,

            "message":
                "Enter an IP address."

        }), 400


    try:

        ip_object =
            ipaddress.ip_address(
                ip
            )

    except ValueError:

        return jsonify({

            "success": False,

            "message":
                "Invalid IP address."

        }), 400


    ip_type = "Public"

    if ip_object.is_private:

        ip_type = "Private"

    elif ip_object.is_loopback:

        ip_type = "Loopback"

    elif ip_object.is_reserved:

        ip_type = "Reserved"


    return jsonify({

        "success": True,

        "ip": ip,

        "type":
            ip_type,

        "status":
            "Valid IP address",

        "country": None,

        "note":
            "VOID INTEL-V2 validated the IP. "
            "An external trusted IP-information "
            "service is required for live geographic "
            "and network information."

    })


# ============================================================
# COUNTRIES API
# ============================================================

@app.route("/api/countries")
def countries():

    search =
        request.args.get(
            "search",
            ""
        ).strip().lower()


    if search:

        results = [

            country

            for country in COUNTRIES

            if
            search in country["name"].lower()
            or
            search == country["code"].lower()

        ]

    else:

        results = COUNTRIES


    return jsonify({

        "success": True,

        "count":
            len(results),

        "countries":
            results

    })


# ============================================================
# SYSTEM INFORMATION
# ============================================================

@app.route("/api/system")
def system_info():

    try:

        memory =
            psutil.virtual_memory()


        disk =
            shutil.disk_usage("/")


        return jsonify({

            "success": True,

            "system":
                platform.system(),

            "release":
                platform.release(),

            "version":
                platform.version(),

            "machine":
                platform.machine(),

            "processor":
                platform.processor(),

            "hostname":
                socket.gethostname(),

            "cpu_percent":
                psutil.cpu_percent(
                    interval=0.5
                ),

            "memory_percent":
                memory.percent,

            "memory_total_gb":
                round(
                    memory.total /
                    (1024 ** 3),
                    2
                ),

            "memory_used_gb":
                round(
                    memory.used /
                    (1024 ** 3),
                    2
                ),

            "disk_total_gb":
                round(
                    disk.total /
                    (1024 ** 3),
                    2
                ),

            "disk_used_gb":
                round(
                    disk.used /
                    (1024 ** 3),
                    2
                ),

            "disk_free_gb":
                round(
                    disk.free /
                    (1024 ** 3),
                    2
                )

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


# ============================================================
# FIREWALL
# ============================================================

@app.route("/api/firewall")
def firewall_status():

    operating_system =
        platform.system()


    try:

        if operating_system == "Windows":

            result =
                subprocess.run(
                    [
                        "netsh",
                        "advfirewall",
                        "show",
                        "allprofiles"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )


            output =
                result.stdout


            enabled =
                "STATE" in output.upper() and \
                "ON" in output.upper()


            return jsonify({

                "success": True,

                "platform":
                    "Windows",

                "firewall":
                    "ACTIVE"
                    if enabled
                    else
                    "CHECK REQUIRED",

                "details":
                    output[:5000]

            })


        if operating_system == "Linux":

            result =
                subprocess.run(
                    [
                        "ufw",
                        "status"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )


            return jsonify({

                "success": True,

                "platform":
                    "Linux",

                "firewall":
                    result.stdout[:2000],

                "details":
                    result.stdout[:5000]

            })


        return jsonify({

            "success": True,

            "platform":
                operating_system,

            "firewall":
                "Automatic check unavailable.",

            "details":
                ""

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


# ============================================================
# ADMIN USERS
# ============================================================

@app.route("/api/admin/users")
def admin_users():

    if not session.get(
        "is_admin",
        False
    ):

        return jsonify({

            "success": False,

            "message":
                "Administrator access required."

        }), 403


    connection =
        get_db()


    users =
        connection.execute(
            """
            SELECT
                id,
                username,
                email,
                is_admin,
                created_at
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()


    connection.close()


    return jsonify({

        "success": True,

        "users":
            [dict(user) for user in users]

    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port =
        int(
            os.environ.get(
                "PORT",
                5000
            )
        )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
