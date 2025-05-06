# AirGhost Phishing Templates

This document provides information about the phishing templates included with AirGhost and how they have been modified to work with the captive portal system.

## Template Modifications

All templates have been modified to:

1. Use a consistent file structure with `index.html` as the main file
2. Include a `config.json` file that defines credential fields and redirect URL
3. Change form actions to point to `/captive/login` instead of PHP files
4. Add JavaScript to handle form submissions via the fetch API
5. Remove unnecessary files (PHP files, documentation, etc.)

## Template Structure

Each template follows this structure:

- **index.html**: The main portal page with the login form
- **config.json**: Configuration file with credential fields and redirect URL
- **assets/**: Directory containing CSS, JavaScript, images, and other assets

### config.json Format

```json
{
  "credentials": [
    {"name": "username", "type": "text"},
    {"name": "password", "type": "password"}
  ],
  "redirect": "https://www.google.com/"
}
```

The `credentials` array defines the form fields that will be captured, and the `redirect` URL is where users will be sent after submitting their credentials.

### Form Submission

Each template's form has been modified to:

1. Set the form action to `/captive/login`
2. Prevent the default form submission with JavaScript
3. Collect form data and submit it via fetch API
4. Redirect the user based on the response from the server

## Available Templates

AirGhost includes the following phishing templates:

1. Adobe
2. Badoo
3. DeviantArt
4. Discord
5. Dropbox
6. Facebook
7. Facebook Advanced
8. Facebook Messenger
9. Facebook Security
10. GitHub
11. GitLab
12. Google
13. Google New
14. Google Poll
15. Instagram
16. Instagram Followers
17. Instagram Verify
18. LinkedIn
19. MediaFire
20. Microsoft
21. Netflix
22. Origin
23. PayPal
24. Pinterest
25. PlayStation
26. ProtonMail
27. Quora
28. Reddit
29. Roblox
30. Snapchat
31. Spotify
32. StackOverflow
33. Steam
34. TikTok
35. Twitch
36. Twitter
37. VK
38. VK Poll
39. WordPress
40. Yahoo
41. Yandex

## Adding Custom Templates

To add a custom template:

1. Create a new directory in the `templates` folder
2. Add an `index.html` file with your login form
3. Set the form action to `/captive/login`
4. Add a `config.json` file with the credential fields and redirect URL
5. Add any necessary assets (CSS, JavaScript, images)

## Legal Disclaimer

These templates are provided for educational and ethical penetration testing purposes only. Always obtain proper authorization before conducting any security tests. The authors are not responsible for any misuse or damage caused by these templates.
