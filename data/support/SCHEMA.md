# Support directory: data format

One CSV per state/UT in `data/support/states/<slug>.csv` (slug = lower-case state name, spaces
and `&` as `-`, e.g. `tamil-nadu.csv`, `jammu-kashmir.csv`), plus `data/support/national.csv`
and `data/support/ngos.csv`. UTF-8, comma-separated, header row exactly:

```
level,state,district,category,name,phones,whatsapp,email,website,address,hours,notes,source_url,verified_on
```

| column | meaning |
|---|---|
| level | `national`, `state` or `district` |
| state | Map state name, exactly one of: Andaman & Nicobar, Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chandigarh, Chhattisgarh, Dadra & Nagar Haveli, Daman & Diu, Delhi, Goa, Gujarat, Haryana, Himachal Pradesh, Jammu & Kashmir, Jharkhand, Karnataka, Kerala, Ladakh, Lakshadweep, Madhya Pradesh, Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Puducherry, Punjab, Rajasthan, Sikkim, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal. Empty for national rows. |
| district | District name as the source spells it (the build script matches it to the map). Empty for state/national rows. |
| category | One of: `emergency`, `women_helpline`, `one_stop_centre`, `legal_aid`, `police_women`, `commission`, `child`, `cyber`, `mental_health`, `shelter`, `protection_officer`, `ngo` |
| name | Organisation or office name, e.g. `Sakhi One Stop Centre, Pune` or `District Legal Services Authority, Pune`. Never a person's name. |
| phones | Phone numbers separated by `; ` as published, e.g. `020-26123456; 9876543210`. Toll-free/short codes as written (`181`, `15100`). |
| whatsapp | WhatsApp number if officially published, else empty |
| email | Official email(s), `; `-separated |
| website | Official page for this office or organisation |
| address | Postal address as published |
| hours | e.g. `24x7`, `10:00-17:00 Mon-Sat`, empty if not stated |
| notes | Services offered (shelter, medical, legal, counselling, police help), languages, anything a woman in crisis should know; also `source dated 2021` etc. if the source is old |
| source_url | The exact page or PDF the row was taken from |
| verified_on | Date the source was checked, `YYYY-MM-DD` |

## Rules

1. **Accuracy over coverage.** Only record contacts you read in the source. Never guess, complete
   or "fix" a number. If a number looks garbled in the source, leave it out and say so in notes.
2. **Government entries come from government sources**: `*.gov.in`, `*.nic.in`, `*.nalsa.gov.in`,
   state police / women & child development / legal services authority sites, or official PDFs
   hosted there. Prefer the most recent document; note its date if it's old.
3. **No personal names** (administrators, secretaries, officers). Keep the office's numbers and
   emails, including a post-holder's official mobile if the government publishes it as the
   contact for that office.
4. NGOs: only registered organisations whose own website publishes the contact, and that work on
   violence against women or girls (helplines, shelters, legal aid, counselling). Cite their site.
5. Quote CSV fields that contain commas.
