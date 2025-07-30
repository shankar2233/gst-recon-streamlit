<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Contact Us</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Poppins', sans-serif;
    }

    body {
      background: linear-gradient(to right, #f2f2f2, #e0f7fa);
      min-height: 100vh;
      padding: 40px 20px;
      color: #333;
      animation: fadeIn 1s ease-in-out;
    }

    @keyframes fadeIn {
      0% { opacity: 0; transform: translateY(20px); }
      100% { opacity: 1; transform: translateY(0); }
    }

    .container {
      max-width: 700px;
      margin: 0 auto;
      background: #fff;
      padding: 30px;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
      animation: fadeIn 1.2s ease-in-out;
    }

    h1 {
      font-size: 2.5rem;
      font-weight: 800;
      text-align: center;
      color: #00796b;
      margin-bottom: 10px;
    }

    .subheading {
      text-align: center;
      font-size: 1.1rem;
      color: #555;
      margin-bottom: 30px;
      animation: fadeIn 1.4s ease-in-out;
    }

    .info-block {
      margin-bottom: 20px;
      animation: fadeIn 1.6s ease-in-out;
    }

    .info-block strong {
      display: block;
      font-size: 1.1rem;
      margin-bottom: 5px;
      color: #00796b;
    }

    a {
      color: #00695c;
      text-decoration: none;
      font-weight: 600;
    }

    a:hover {
      text-decoration: underline;
    }

    .email-button {
      display: inline-block;
      margin-top: 20px;
      padding: 12px 25px;
      background: linear-gradient(135deg, #26c6da, #00acc1);
      color: white;
      border-radius: 30px;
      text-decoration: none;
      font-weight: 600;
      transition: background 0.3s ease;
      animation: fadeIn 1.8s ease-in-out;
    }

    .email-button:hover {
      background: linear-gradient(135deg, #00acc1, #00838f);
    }

    .support-hours {
      margin-top: 30px;
      animation: fadeIn 2s ease-in-out;
    }

    .quick-actions {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 25px;
      animation: fadeIn 2.2s ease-in-out;
    }

    .quick-actions a {
      display: inline-block;
      padding: 12px;
      background: #eeeeee;
      border-radius: 8px;
      text-align: center;
      font-weight: 600;
      transition: background 0.3s ease;
    }

    .quick-actions a:hover {
      background: #d0f0f4;
    }

    @media (max-width: 500px) {
      h1 {
        font-size: 2rem;
      }

      .container {
        padding: 20px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>📞 Get in Touch</h1>
    <div class="subheading">We're here to help! Reach out with questions, feedback, or support needs.</div>

    <div class="info-block">
      <strong>📧 Email Support</strong>
      General Inquiries: <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a><br>
      Technical Issues: <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a>
    </div>

    <div class="info-block">
      <strong>⏱️ Response Time:</strong>
      Within 24 hours
    </div>

    <a href="mailto:riaskingofanime@gmail.com" class="email-button">Send Email Now ✉️</a>

    <div class="support-hours">
      <strong>🕐 Support Hours</strong><br>
      Monday – Friday: 9:00 AM – 6:00 PM (IST)<br>
      Saturday: 10:00 AM – 4:00 PM (IST)<br>
      Sunday: Closed
    </div>

    <div class="quick-actions">
      <a href="mailto:riaskingofanime@gmail.com?subject=General Inquiry">💬 General Support</a>
      <a href="mailto:riaskingofanime@gmail.com?subject=Technical Issue">🔧 Technical Help</a>
      <a href="mailto:riaskingofanime@gmail.com?subject=Feedback">⭐ Send Feedback</a>
    </div>
  </div>
</body>
</html>
