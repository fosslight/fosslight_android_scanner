# Changelog

## v5.0.15 (10/07/2026)
## Changes
## 🔧 Maintenance

- Align report and log timestamps with fosslight_util time helpers @bjk7119 (#62)
- Migrate to REUSE.toml and update GitHub Actions @woocheol-lge (#61)
- Add LGE_NOTICE.txt for testing @soimkim (#60)

---

## v5.0.14 (14/05/2026)
## Changes
## 🚀 Features

- Print platform version from AOSP repo manifest @soimkim (#59)

## 🔧 Maintenance

- Add scanner version log at startup @woocheol-lge (#58)

---

## v5.0.13 (09/04/2026)
## Changes
## 🔧 Maintenance

- Update missing notice file message and notice zip filename @soimkim (#57)
- Update help message format for FOSSLight Android Scanner @bjk7119 (#55)
- feat(python): add Python 3.13/3.14 support @soimkim (#56)
- Remove "Type of change" section from PR default template @woocheol-lge (#54)

---

## v5.0.12 (26/02/2026)
## Changes
## 🔧 Maintenance

- Update version requirements for FOSSLight packages  @soimkim (#53)
- Add .coderabbit.yaml configuration file for review @soimkim (#52)

---

## v5.0.11 (24/09/2025)
## Changes
## 🐛 Hotfixes

- Find build output path from new format build log @soimkim (#50)

---

## v5.0.10 (31/07/2025)
## Changes
## 🐛 Hotfixes

- Print download location without checking new binary @soimkim (#49)

---

## v5.0.9 (17/07/2025)
## Changes
## 🔧 Maintenance

- Update setup.py @ethanleelge (#48)

---

## v5.0.8 (17/07/2025)
## Changes
## 🔧 Maintenance

- Update setup.py @ethanleelge (#47)
- Keep the line "Programming Language :: Python :: 3" in setup.py
---

## v5.0.7 (17/07/2025)
## Changes
## 🔧 Maintenance

- Modify setup.py to change the supported Python version to 3.10 - 3.12 @ethanleelge (#46)

---

## v5.0.6 (28/03/2025)
## Changes
## 🔧 Maintenance

- Remove unnecessaries @ethanleelge (#44)
- Remove unnecessary options in help msg @ethanleelge (#42)

---

## v5.0.5 (05/03/2025)
## Changes
## 🔧 Maintenance

- Remove some options (-b, -n, -c, -t, -d) @ethanleelge (#41)



---

## v5.0.4 (25/02/2025)
## Changes
## 🚀 Features

- Compressing the notice files @ethanleelge  (#38)

---

## v5.0.3 (12/02/2025)
## Changes
## 🐛 Hotfixes

- Add exception handling for cases where the 'installed' key is not present @ethanleelge (#36)

## 🔧 Maintenance

- Fix the platform version as an integer @ethanleelge (#35)
- Update message format when module-info.json cannot be read @soimkim (#34)

---

## v5.0.2 (17/01/2025)
## Changes
## 🐛 Hotfixes

- Update FOSSLight Util version for fixing m option bug @soimkim (#32)
- Fix source code analysis bug @soimkim (#31)
- Fixe a bug that checks if it's binary or not @soimkim (#29)

## 🔧 Maintenance

- Remove NOTICE.txt from Notice file list in log @soimkim (#30)

---

## v5.0.1 (01/11/2024)
## Changes
## 🔧 Maintenance

- Update requirements.txt @dd-jy (#28)
- Print option name with error msg @bjk7119 (#27)
- Refactor existing tox test to pytest @ena-isme (#24)

---

## v5.0.0 (08/09/2024)
## Changes
## 🔧 Maintenance

- Refactoring related to FOSSLight Util @soimkim (#21)
- Revert android_binary_analysis @soimkim (#20)
- Remove the Unused Option from Run Parameters @cjho0316 (#18)
- Limit version of fosslight packages @soimkim (#19)

---

## v4.1.19 (10/06/2024)
## Changes
## 🚀 Features

- Add scanner info sheet @dd-jy (#12)

## 🔧 Maintenance

- Update the column name @soimkim (#16)
- Update the information on the cover sheet @soimkim (#15)
- Do not print text file @soimkim (#14)

---

## v4.1.18 (21/05/2024)
## Changes
## 🚀 Features

- Add paths to exclude from source analysis @soimkim (#11)

---

## v4.1.17 (08/04/2024)
## Changes
## 🚀 Features

- Add TLSH, SHA1 column at report @bjk7119 (#10)

## 🔧 Maintenance

- Use common github actions @bjk7119 (#9)

---

## v4.1.16 (06/11/2023)
## Changes
## 🔧 Maintenance

- Remove unwanted log @JustinWonjaePark (#8)

---

## v4.1.15 (30/10/2023)
## Changes
## 🔧 Maintenance

- Upgrade Python minimum version to 3.8 @JustinWonjaePark (#7)
- Fix the vulnerability @dd-jy (#6)

---

## v4.1.14 (09/06/2023)
## Changes
## 🚀 Features

- Unzip NOTICE files ending with gz @soimkim (#5)

## 🔧 Maintenance

- Update the ubuntu version for deploy action @dd-jy (#4)

---

## v4.1.13 (27/02/2023)
## Changes
## 🐛 Hotfixes

- Fix a bug related to need_check @soimkim (#3)

---

## v4.1.12 (24/02/2023)
## Changes
## 🔧 Maintenance

- Update output file names @soimkim (#2)