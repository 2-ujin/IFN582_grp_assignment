# MakeArtsFund shared style guide

Use this guide on every page so the application follows the Assessment 1 design.

## Visual system

- Charcoal #25242a for primary text and dark surfaces.
- Coral #e76f51 for primary actions and highlights; use coral-dark #c9553b for text links and hover states.
- Cream #fffaf5 for the page background, white #ffffff for cards, and tint #f7f0ea for secondary panels.
- Ash #727078 for supporting text and line #eadfd6 for borders.
- DM Sans for interface text; Playfair Display for page and section headings.

## Components

- Use rounded pill buttons. Primary actions use coral; secondary actions use a coral outline.
- Use white cards with a fine line border, generous padding, and a restrained shadow.
- Keep form labels visible, inputs at least 44px high, and validation feedback beside the relevant field.
- Use the shared navbar, flash-message area, footer, skip link, and stylesheet through base.html.
- The login, registration, and error templates override the header_navigation block; this keeps the logo and English selector while hiding site links on those pages.
- Keep the footer links in the Assessment 1 order: About, Contact Us, Terms, Press.
- Add page-specific role links through the role_navigation block in base.html so future routes do not break pages that are not ready yet.
- Keep layouts responsive with Bootstrap grid utilities and the shared breakpoints. The navigation wraps on smaller screens and does not require JavaScript.
- Keep text readable against its background and preserve visible keyboard focus styles.

## Integration

- Extend base.html for every page and provide a page title.
- Use the shared button, coral-button, outlined-coral-button, section-padding, and section-tint classes where appropriate.
- Use Bootstrap 5.3 CSS and the existing stylesheet. Do not add custom JavaScript or external themes.
