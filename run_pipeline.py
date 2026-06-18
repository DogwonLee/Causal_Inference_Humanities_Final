"""
Run the full six-step pipeline end to end.

    python run_pipeline.py

Each step writes its artifacts to outputs/ (and figures/). The steps are
independent modules so they can also be run one at a time for inspection.
"""
from src import clean_newspapers, extract_ekg, build_graph, causal_model, inference, confounding_demo


def main():
    print("\n=== Step 1-2: clean & segment =========================")
    clean_newspapers.run()
    print("\n=== Step 3: extract entities/events/causal assertions ==")
    extract_ekg.extract()
    print("\n=== Step 4: build knowledge graph =====================")
    g = build_graph.build()
    build_graph.summarize(g)
    build_graph.export(g)
    print("\n=== Step 5: build causal DAG + figure =================")
    dag = causal_model.build_dag()
    Z, bdoor = causal_model.find_adjustment_set(dag, "T", "O")
    print("backdoor paths:", [" - ".join(p) for p in bdoor])
    print("adjustment set:", Z)
    causal_model.render(dag)
    print("\n=== Step 6: causal inference ==========================")
    inference.run()
    print("\n=== Step 6 (quant add-on): confounding demo ===========")
    confounding_demo.run()
    print("\nDone. See outputs/ and figures/.")


if __name__ == "__main__":
    main()
