#!/usr/bin/env python
"""Parse the canonical ChemOnt 2.1 OBO into nodes/edges/lineage (Layer A).

Layer A of the v5 architecture: the complete ChemOnt 2.1 ontology is the immutable
canonical taxonomy backbone. This script parses the *actual supplied* OBO and
validates its topology rather than assuming it. Outputs:

  database/v4/chemont_nodes.tsv    id, name, definition, parent_id, depth, is_obsolete, n_ancestors
  database/v4/chemont_edges.tsv    parent_id, child_id (is_a)
  database/v4/chemont_lineage.json {chemont_id: [self, parent, ... root]}
  reports/v4/chemont_topology.json validation summary

No network. Deterministic. Does not modify the OBO.
"""
import json, re, sys, collections, pathlib

ROOT = pathlib.Path("/data01/cris/projects/DAG")
OBO = ROOT / "data/external/chemont/ChemOnt_2_1.obo"
DBDIR = ROOT / "database/v4"; DBDIR.mkdir(parents=True, exist_ok=True)
REPDIR = ROOT / "reports/v4"; REPDIR.mkdir(parents=True, exist_ok=True)


def parse_obo(path):
    terms = {}
    cur = None
    data_version = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("data-version:") and data_version is None:
                data_version = line.split(":", 1)[1].strip()
            if line == "[Term]":
                if cur is not None and cur.get("id"):
                    terms[cur["id"]] = cur
                cur = {"id": None, "name": None, "def": None, "parents": [], "obsolete": False}
                continue
            if line.startswith("[") and line != "[Term]":
                # leaving Term stanzas (e.g. [Typedef])
                if cur is not None and cur.get("id"):
                    terms[cur["id"]] = cur
                cur = None
                continue
            if cur is None:
                continue
            if line.startswith("id:"):
                cur["id"] = line.split(":", 1)[1].strip()
            elif line.startswith("name:"):
                cur["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("def:"):
                m = re.search(r'"(.*)"', line)
                cur["def"] = m.group(1) if m else line.split(":", 1)[1].strip()
            elif line.startswith("is_a:"):
                # is_a: CHEMONTID:0000000 ! Organic compounds
                val = line.split(":", 1)[1].strip()
                pid = val.split("!")[0].strip()
                cur["parents"].append(pid)
            elif line.startswith("is_obsolete:") and "true" in line.lower():
                cur["obsolete"] = True
        if cur is not None and cur.get("id"):
            terms[cur["id"]] = cur
    return terms, data_version


def main():
    terms, data_version = parse_obo(OBO)
    ids = set(terms)
    # roots = terms with no parents
    roots = [t for t, d in terms.items() if not d["parents"]]
    # multi-parent nodes
    multi = [t for t, d in terms.items() if len(d["parents"]) > 1]
    # dangling parents (parent id not a known term)
    dangling = sorted({p for d in terms.values() for p in d["parents"] if p not in ids})

    # ancestor lineage via memoized walk; detect cycles
    lineage = {}
    WHITE, GREY, BLACK = 0, 1, 2
    color = {t: WHITE for t in terms}
    cycle_nodes = []

    def walk(t, stack):
        if color[t] == BLACK:
            return lineage[t]
        if color[t] == GREY:
            cycle_nodes.append(t)
            return [t]
        color[t] = GREY
        parents = terms[t]["parents"]
        if not parents:
            lin = [t]
        else:
            # primary parent = first is_a; lineage follows primary chain to root
            p = parents[0]
            if p in terms:
                lin = [t] + walk(p, stack + [t])
            else:
                lin = [t]
        lineage[t] = lin
        color[t] = BLACK
        return lin

    for t in terms:
        if color[t] == WHITE:
            walk(t, [])

    depths = {t: len(lineage[t]) - 1 for t in terms}
    obsolete = [t for t, d in terms.items() if d["obsolete"]]

    # write nodes
    with open(DBDIR / "chemont_nodes.tsv", "w", encoding="utf-8") as fh:
        fh.write("chemont_id\tname\tdefinition\tparent_id\tdepth\tis_obsolete\tn_ancestors\n")
        for t in sorted(terms):
            d = terms[t]
            parent = d["parents"][0] if d["parents"] else ""
            name = (d["name"] or "").replace("\t", " ")
            defi = (d["def"] or "").replace("\t", " ").replace("\n", " ")
            fh.write(f"{t}\t{name}\t{defi}\t{parent}\t{depths[t]}\t{int(d['obsolete'])}\t{len(lineage[t])-1}\n")

    # write edges (all is_a, including alternative multi-parent)
    with open(DBDIR / "chemont_edges.tsv", "w", encoding="utf-8") as fh:
        fh.write("parent_id\tchild_id\n")
        for t in sorted(terms):
            for p in terms[t]["parents"]:
                fh.write(f"{p}\t{t}\n")

    with open(DBDIR / "chemont_lineage.json", "w", encoding="utf-8") as fh:
        json.dump(lineage, fh)

    depth_hist = collections.Counter(depths.values())
    summary = {
        "obo_path": str(OBO),
        "data_version": data_version,
        "n_terms": len(terms),
        "n_roots": len(roots),
        "roots": roots,
        "n_multi_parent": len(multi),
        "n_edges_is_a": sum(len(d["parents"]) for d in terms.values()),
        "n_obsolete": len(obsolete),
        "n_dangling_parents": len(dangling),
        "dangling_parents": dangling[:50],
        "n_cycle_nodes": len(set(cycle_nodes)),
        "max_depth": max(depths.values()),
        "depth_histogram": {str(k): v for k, v in sorted(depth_hist.items())},
        "acyclic": len(cycle_nodes) == 0,
    }
    with open(REPDIR / "chemont_topology.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
