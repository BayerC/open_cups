## Lessons learned developing the app
- Threading and race condition handling is complex. Double-check code and use AI review to catch bugs.
- Ruff includes many checks. Verify if a check exists before adding new tools.
- Use AGENTS.md to guide LLM behavior. Modify it when responses need adjustment.
- GitHub won't let you turn on automerge per default for PRs, even with the merge queue
- Codecov is free for open source projects
- Streamlit has a [nice testing framework](https://docs.streamlit.io/develop/api-reference/app-testing)
- [There are special GitHub action triggers for fork-based workflows](https://github.com/amannn/action-semantic-pull-request?tab=readme-ov-file#event-triggers)
- GitHub requires explicit configuration of required status checks: Settings → Branches → Branch protection rules → Require status checks to pass before merging
- When vibe coding a complex task, start by discussing the possible solution in `Ask` mode. Only move to `Agent` mode once you’re confident in the approach.
  Jumping straight into large-scale code changes can be misleading and makes it easy to lose track of the correct solution.
- Use `Voice Input` in Cursor to describe complex tasks in a fast and easy way
- Use [Pytest-BDD](https://pytest-bdd.readthedocs.io/en/stable/#) for integration tests to document the user interface
- One can connect [Claude AI](https://claude.ai) to GitHub so it can browse your repository and collaborate with you.
- A retro is very important in an async remote team collaboration
- [Python overloading](https://stackoverflow.com/a/54423390/7260972) is just a type hint and doesn't really allow defining two separate overloads.
  That requires usage of hacks such as `isinstance()`, which makes overloads not attractive
- [Google NotebookLM](https://notebooklm.google.com/) is a great tool for ai generated one pager ("Infographic") or slides ("Slide Deck"). Note that one can customize the prompt using the edit symbol.
