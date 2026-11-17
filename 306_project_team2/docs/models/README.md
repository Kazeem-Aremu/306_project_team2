# Team A2 UML models

Source files for the six diagrams in "Team A2 Requirements and Models".
Put this folder in the repo at docs/models/.

| Diagram | Source | Tool |
|---|---|---|
| Context | 01_context.dot | Graphviz: `dot -Tpng 01_context.dot -o 01_context.png` |
| Use case | 02_usecase.dot | Graphviz: `neato -Tpng 02_usecase.dot -o 02_usecase.png` |
| Activity | 03_activity.mmd | Mermaid: paste into https://mermaid.live or `mmdc -i 03_activity.mmd -o 03_activity.png` |
| Class | 04_class.mmd | Mermaid |
| State | 05_state.dot | Graphviz: `dot -Tpng 05_state.dot -o 05_state.png` |
| Sequence | 06_sequence.mmd | Mermaid |

Graphviz files can also be edited online at https://dreampuf.github.io/GraphvizOnline

Also included (images only, drawn in the UML Diagrams and Architecture Rationale doc):
- 07_architecture.png - four-layer architecture
- 08_ui_design.png - browser UI: sign-in, requester, coordinator, technician and summary screens (NFR-01)

Note: "Technician" in these diagrams is the role the guide and traceability table call "service staff".
