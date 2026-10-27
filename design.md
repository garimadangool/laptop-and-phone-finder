I want you to redesign the UI of my existing laptop recommendation system.

IMPORTANT:
- First inspect the existing project structure, especially ui/app.py and any related CSS/components/assets.
- Understand the existing functionality before making changes.
- Do NOT remove or break any existing backend, ML recommendation logic, API calls, data processing, or functionality.
- Focus primarily on improving the frontend/UI/UX.

DESIGN GOAL:
Create a unique, modern, simple, pretty, interactive and welcoming laptop recommendation interface.

The UI should NOT feel like:
- A bank form
- A government website
- A boring admin dashboard
- A generic AI template
- A basic Streamlit application
- A page full of plain text inputs and dropdowns

Instead, it should feel like:
- A friendly personal laptop shopping assistant
- Comfortable and easy to use
- Modern and slightly playful
- Premium but not overly complicated
- Something a student or normal laptop buyer would actually enjoy using

VISUAL STYLE:
- Use a light theme only.
- Do NOT use dark mode.
- Do NOT use extremely bright/neon colours.
- Avoid excessive gradients.
- Use a soft, sophisticated colour palette with good contrast.
- The colours should be accessible for colour-blind users.
- Do not rely on colour alone to communicate information.
- Use icons, labels, shapes, text and visual hierarchy in addition to colour.
- Use plenty of whitespace.
- Use rounded cards and subtle shadows.
- Keep the interface clean rather than cluttered.
- Use a consistent design system throughout the application.
- Typography should be modern, readable and friendly.

COLOUR DIRECTION:
Use a restrained accessible palette such as:
- soft off-white/light background
- dark charcoal text
- muted blue/teal or blue/purple accents
- subtle secondary colours
- gentle borders
- accessible contrast

Do not use:
- pure white everywhere
- neon green
- neon purple
- excessive blue
- rainbow colours
- very saturated backgrounds
- colour combinations that are difficult for colour-blind users

UX:
The user should feel guided rather than interrogated.

Instead of presenting a huge form at once, make the recommendation process feel natural and easy.

For example, organize the experience around simple sections/cards such as:

1. "What are you looking for?"
   - Purpose cards such as:
     Student
     Gaming
     Programming
     Creative Work
     Business
     Everyday Use

2. "What's your budget?"
   - Make the budget selection visually friendly.
   - Use NPR because this system is designed for Nepali users.

3. "What matters most to you?"
   - RAM
   - Storage
   - Processor
   - GPU
   - Brand
   - Battery/portability if supported by the existing dataset

Use cards, segmented controls, chips, icons, sliders or other visually pleasant controls where appropriate instead of making everything look like traditional forms.

INTERACTION:
Make the interface feel interactive and responsive.

Examples:
- Hover effects on cards/buttons where possible
- Clear selected states
- Smooth visual feedback
- Recommendation loading state
- Friendly empty states
- Helpful explanations/tooltips
- Clear validation messages
- "Why this laptop?" explanations for recommendations
- Visually distinguish recommended/top matches
- Allow users to easily change preferences and search again

LAPTOP RESULTS:
The recommendation results should look like actual product recommendations rather than rows in a spreadsheet.

Each laptop result should ideally have:
- Laptop image if available
- Product/laptop name
- Price in NPR
- Important specifications
- Recommendation/match score if available
- Short reason why it matches the user's requirements
- Clear action/button
- Visually highlight the best match

Use attractive product cards rather than a plain dataframe whenever possible.

IMAGES:
Images can be used where they genuinely improve the experience.

For example:
- Laptop/product images
- Small category illustrations
- Subtle decorative illustrations

Do NOT overload the page with images.
Images should support the UI rather than make it look like an advertisement.

ACCESSIBILITY:
Accessibility is important.

- Use accessible colour contrast.
- Design for colour-blind users.
- Never communicate meaning using colour alone.
- Use readable font sizes.
- Make buttons and interactive controls easy to identify.
- Keep labels clear.
- Avoid tiny text.
- Maintain logical keyboard/navigation structure where possible.
- Make selected/unselected states obvious through borders, icons, text and shape as well as colour.

RESPONSIVE DESIGN:
The interface should work well on:
- Desktop
- Laptop screens
- Smaller screens

Avoid layouts that become extremely wide or cramped.

IMPORTANT TECHNICAL REQUIREMENTS:
- Keep the existing Python/Streamlit architecture unless there is a strong reason to change it.
- Do not unnecessarily introduce React or another frontend framework.
- Reuse the existing recommendation system.
- Do not modify ML logic unless absolutely necessary.
- Keep the code organized and maintainable.
- Put custom styling in a logical place rather than scattering huge amounts of CSS everywhere.
- Avoid unnecessary dependencies.
- Make sure the application still runs with:

streamlit run ui/app.py

Before finishing:
1. Inspect the existing code.
2. Implement the redesign.
3. Run/check the application for errors.
4. Fix any UI or Python errors you introduce.
5. Make sure the recommendation functionality still works.
6. Give me a short summary of what you changed.

The final result should feel like a polished AI-powered laptop shopping assistant for Nepali users — friendly, modern, comfortable, accessible, interactive and visually distinctive, while still being simple to understand.


The ui must feel like an actual site already implemented not just for the project also update the logbook.md all development tasks done until now 