# Field Precedence

| Source | Default confidence band | Notes |
|---|---:|---|
| JSON-LD | 0.90–1.00 | explicit structured page data |
| Next.js state | 0.90–1.00 | site application state |
| Visible HTML | 0.75–0.95 | labels and text blocks |
| OCR | 0.45–0.80 | digit/text recognition risk |
| Vision | 0.45–0.80 | useful for poster-only content |
| Fallback/manual | explicit | must be identified |

Do not select a value only because its numeric confidence is marginally higher when the source is semantically weaker and conflicts with an explicit primary field. Record the conflict for review.
