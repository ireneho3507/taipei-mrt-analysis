# Week 16: MILESTONE — Final Project Presentation

> **Course:** NS5116 Programming & AI Applications in Behavioral Science — Spring 2026
> **Week:** 16 of 16 | **Date:** 2026-06-18 | **Room:** TBA

---

## Overview

This is the final class of the course — a public symposium. Every student presents their completed web application to the class. You will give a live 10-minute demo of a deployed Streamlit app that uses real Taiwan open data and at least one AI feature built with the Claude API.

There is no new programming content this week. Your app should be fully deployed, your presentation rehearsed, and your submission checklist complete before you arrive.

---

## What You Are Presenting

Your final project is a publicly accessible web application that demonstrates every major skill from Part 2 of the course:

| Requirement | Tool | Covered in |
|-------------|------|-----------|
| Web application | Streamlit | Week 11 |
| Real Taiwan open data | data.gov.tw or EPA API | Week 12 |
| Interactive charts | Plotly Express | Week 13 |
| AI feature | Claude API | Week 14 |
| Automated tests | pytest + GitHub Actions | Week 10 |
| Public deployment | Streamlit Cloud | Weeks 11, 15 |

---

## Presentation Format

**Duration:** 10 minutes total — 8 minutes demo + 2 minutes Q&A

**Order:** Determined by random draw in class. Check the board when you arrive.

**Equipment:** Use your own laptop connected to the classroom projector. Have the Streamlit Cloud URL open and ready before your slot begins.

| Section | Time | What to cover |
|---------|------|--------------|
| Problem and data source | 1.5 min | What question does your app answer? What dataset did you use and why? |
| Live demo | 4.5 min | Demonstrate the app working: at least one filter, one chart, the AI feature |
| Key finding | 1.0 min | What did you discover from the data? State one concrete result. |
| Reflection | 1.0 min | What was the hardest technical challenge? What would you build next? |
| Q&A | 2.0 min | Answer two questions from the audience or instructor |

**Demo tips:**
- Open the Streamlit Cloud URL before your presentation slot — do not wait for the page to load during your time
- Show the app in a browser, not VS Code or the terminal
- Narrate what you are clicking and why ("I'll filter to Taipei County to show...")
- If something breaks: close the browser tab, reopen the URL, and continue calmly

---

## Submission Checklist

Submit before 9:00 AM on presentation day. Late submissions cannot be graded.

```
DEPLOYMENT
[ ] App loads at the Streamlit Cloud URL (test in incognito mode)
[ ] App loads without errors in Chrome and Firefox
[ ] All charts render correctly
[ ] AI chat feature works (API key in st.secrets)
[ ] App loads in under 20 seconds (first load after sleep may be slower)

GITHUB REPOSITORY
[ ] Repository is public and accessible
[ ] README is complete: title, data source, features, run instructions, limitations
[ ] requirements.txt is present and up to date
[ ] .gitignore includes .env and secrets.toml
[ ] No API keys, passwords, or personal data in any committed file
[ ] At least one passing GitHub Actions test run visible in the Actions tab

DATA
[ ] Real Taiwan open data is used (not just a demo dataset)
[ ] Data source is documented in the README (name, URL, date range)

PRESENTATION
[ ] Streamlit Cloud URL ready to paste into chat if audience wants to try it
[ ] Laptop charged; display connection cable available
[ ] Presentation rehearsed and timed at 8 minutes
```

---

## Grading Rubric

| Criterion | Points | Description |
|-----------|--------|-------------|
| App runs without errors | 25 | The deployed app completes all demonstrated interactions without crashing |
| Real Taiwan open data used meaningfully | 20 | Data is from a Taiwan government source; the analysis produces a genuine insight |
| Interactive features | 15 | At least two working widgets that change the chart or table output |
| Visualizations are clear and appropriate | 15 | Charts have labelled axes, units, and at least one annotation or reference line |
| AI feature adds genuine value | 15 | The Claude API feature helps users understand or explore the data |
| Presentation clarity | 10 | Problem stated, demo fluent, one concrete finding presented |
| **Total** | **100** | |

**Deductions:**
- −10 if the app requires a login or is not publicly accessible
- −10 if API keys are found in the git history (check with `git log -p | grep "sk-ant"`)
- −5 if `requirements.txt` is missing or incomplete (app fails to deploy fresh)

---

## Project Examples by Topic

These are example project directions — your project may follow a different topic entirely.

| Topic | Data source | Example question |
|-------|-------------|-----------------|
| Air quality | Taiwan EPA `aqx_p_432` | Which counties consistently exceed WHO PM2.5 guidelines? |
| Earthquakes | CWA open data | How has earthquake frequency near the east coast changed over the last decade? |
| Hospital access | data.gov.tw | How does the ratio of hospitals to population vary by township? |
| Transit ridership | TRA / MRT open data | Which MRT lines recovered fastest after the 2021 earthquake? |
| Water quality | EPA river monitoring | Which river basins show improving BOD trends since 2015? |

---

## After the Course

Your project does not have to stop here. Practical next steps:

1. **Add more data.** Add a second dataset from the same portal and merge it with `pd.merge()`.
2. **Automate refresh.** Use a GitHub Actions scheduled workflow to pull fresh data nightly and push the updated cache to the repository.
3. **Open source.** Add an MIT or CC0 license so others can use your code and data pipeline.
4. **Share your work.** Add the Streamlit Cloud URL to your GitHub profile README and LinkedIn. A deployed, working application is a more compelling portfolio item than a notebook.
5. **Continue building.** The skills from Part 2 of this course — agentic coding, open data APIs, Streamlit, Claude API — apply to virtually any data-driven application you want to build.

---

## Resources

- [Streamlit Community Cloud documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [GitHub Actions — scheduled workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
- [Taiwan open data portal](https://data.gov.tw/en)
- [Claude API documentation](https://docs.anthropic.com/en/api/getting-started)
- [Choose a license](https://choosealicense.com/)

---

## Course Summary

| Part | Weeks | What you built | Key skills |
|------|-------|---------------|------------|
| Manual Python | 1–5 | Data analysis scripts and plots | Python syntax, NumPy, Matplotlib |
| PsychoPy | 6–7 | Spatial-cueing experiment | Stimulus presentation, RT measurement, trial design |
| Midterm | 8 | Online experiment on Pavlovia | Web deployment, data collection, analysis presentation |
| Vibe Coding | 9–10 | Project scaffold with tests and CI | Claude Code, git branching, pytest, GitHub Actions |
| Web app | 11–13 | Streamlit dashboard with Plotly charts | Widgets, caching, interactive visualization |
| AI features | 14 | Claude API chatbot in Streamlit | System prompts, streaming, secrets management |
| Final | 15–16 | Complete deployed web application | End-to-end product: data → app → presentation |
