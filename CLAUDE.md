This project follows the project-docs convention (ROADMAP.md, DECISIONS.md, HANDOFF.md).
When the user asks to resume ("retoma", "vamos continuar o projeto", "vamos continuar o desenvolvimento do roadmap"), before acting: read HANDOFF.md; from ROADMAP.md, only the item titles (`grep -n "^[0-9]\+\. \*\*" ROADMAP.md`), the Order table and the item of the next step or of the request. Confirm the state and the next step in 3 lines and wait for the go-ahead.

How to work here: ROADMAP.md's "How an agent uses this file". Talk with the modeler in Portuguese, with Blender terms in English; code, comments, file names and commits in English.

Commits: only when a piece of work is concluded, when the modeler approves a new feature of the bridge, or at a handoff; not per leaf, review or topic change.

Questions about a spot on the model go inside the review (`review(names, questions=[...])`, marking the ids), not as ids in the chat; describe the AI's own words (rib, crotch, valley, flap) in plain terms.

After changing extension code: copy it into the installed extension (`%APPDATA%/Blender Foundation/Blender/5.2/extensions/user_default/llm_modeling_bridge`) and restart the AI Blender (`extension/fofuxo-bridge/launcher.py`); never hot-reload, and never import `llm_modeling_bridge.<submodule>` through the alias in MCP code (it loads a second copy of the modules).
