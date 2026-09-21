# Kestrel Bay

A grey, rain-soaked fishing town on steep coastal cliffs — an open world built as **data** on the
Gogi `godot-tmpl-rpg` engine (Godot 4.7.1, Compatibility renderer, `nothreads` web export, also
native-playable via `world.json`).

**Play:** https://preview.myapping.com/cloud-q7026dnarajiwk7glrcg/

## The place

- A +26 m cliff-top plateau ringed by a real sea cliff over grey-green water; the **harbour** sits in
  a cove at +2 m with a switchback road climbing to the town.
- The **quay**: harbour office, net shed, boathouse, sheds, hut, quay wall and bollards, a moored
  fishing boat, a battered blue truck, and the fishermen who work there.
- The **town** on the cliff top: High Street with the Kestrel Arms pub, the chandlery, the
  Fishermen's Institute and its square (well, notice board), terraces, townhouses and cottages,
  walled gardens behind, a market hall on the back lane, a warehouse.
- Around it: a wooded belt and copses, walled fields with five farmsteads (farmhouse, barn, stable,
  pigsties), hedged lanes with hawthorn and gorse, heather and rocky moor to the east with two ruined
  **engine houses**, stone circles, sheepfolds and marsh hollows, lookout huts on the cliff tops,
  the **chapel** (nave, porch, chancel, bell tower with spire) on its hill, and the **lighthouse**
  on Kestrel Point.
- Down the coast a second inlet holds the **wreck of the trawler Marguerite** and the **sea caves**
  where the smugglers are holed up.

Ground changes underfoot by biome (cobbles, gravel lanes, mud yards, sand, rock, heather-brown moor
grass); every land cell carries trees, gorse, heather, bracken, boulders or grass matched to it.

## Enterable (Mason-compiled, glazed windows, walk-gate verified)

lighthouse · Kestrel Arms (bar, snug, three rooms upstairs) · harbour office (charts on the desk,
office upstairs) · chandlery (shop + lodging) · net shed · chapel · one house · the market hall ·
the wreck · the sea caves. Every other building is shut.

## People

Meshy-generated characters: the player, harbour master Alwyn behind his desk, Morwenna behind the
bar and Dai on the bench outside the pub door, Old Hal and Jory on the quay benches, Pasco mending a net by the shed,
the lighthouse keeper, the verger in the chapel, wandering villagers, the smugglers and their
ringleader inside the cave. Talk with USE — replies come from the shared NPC brain and are spoken.

## Behaviour is data

`world.json` carries terrain, water, sky cycle, cells (biome, ground, buildings, dressing, scatter,
rows), vehicles, weapons, regions, `rules`/`vars`/`hud` (checkpoint at the cove path, respawn on
death, kill counter) and the `director` (title, quest chain; the run is won by a rule on the finished quest). `quests.json`
holds the two-quest story. `structures.json` holds the 30 Mason building specs. No game scripts —
every `.gd` is the unmodified engine template.

## Build

```bash
/workspace/godot --headless --path . --import
/workspace/godot --headless --path . --export-release "Web" out/index.html
cp world.json quests.json out/ && cp -R models audio out/
```
