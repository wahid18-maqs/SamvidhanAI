/** Section 7: all 22 Eighth Schedule languages plus English, each labeled
 * in its own native script (not transliterated). Retrieval stays English
 * internally — this only controls the language Gemini generates the
 * explanation in (backend/graph/nodes/generation.py's LANGUAGE_NAMES). */
export const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "as", name: "অসমীয়া" },
  { code: "bn", name: "বাংলা" },
  { code: "brx", name: "बड़ो" },
  { code: "doi", name: "डोगरी" },
  { code: "gu", name: "ગુજરાતી" },
  { code: "hi", name: "हिन्दी" },
  { code: "kn", name: "ಕನ್ನಡ" },
  { code: "ks", name: "كٲشُر" },
  { code: "kok", name: "कोंकणी" },
  { code: "mai", name: "मैथिली" },
  { code: "ml", name: "മലയാളം" },
  { code: "mni", name: "ꯃꯩꯇꯩꯂꯣꯟ" },
  { code: "mr", name: "मराठी" },
  { code: "ne", name: "नेपाली" },
  { code: "or", name: "ଓଡ଼ିଆ" },
  { code: "pa", name: "ਪੰਜਾਬੀ" },
  { code: "sa", name: "संस्कृतम्" },
  { code: "sat", name: "ᱥᱟᱱᱛᱟᱲᱤ" },
  { code: "sd", name: "سنڌي" },
  { code: "ta", name: "தமிழ்" },
  { code: "te", name: "తెలుగు" },
  { code: "ur", name: "اردو" },
];

export default function LanguageSelector({ value, onChange }) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      aria-label="Response language"
      className="rounded-full border border-border bg-panel px-2 py-1 text-xs text-body outline-none transition hover:bg-border/40 focus:border-border-strong"
    >
      {LANGUAGES.map((language) => (
        <option key={language.code} value={language.code}>
          {language.name}
        </option>
      ))}
    </select>
  );
}
