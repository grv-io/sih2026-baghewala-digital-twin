# Demo video — 3-minute website walkthrough (voice-over script)

Screen recording: `ppt/final/SIH26120_walkthrough_screen.webm` (made by
`ppt/record_walkthrough.py`, paced to these timestamps). Record the voice-over
over it; ~450 words at a normal pace.

## 0:00–0:25 · Opening (screen: Overview, status chip "Live API")

Oil India's Baghewala field in Rajasthan produces very heavy oil. It only flows
after steam is injected into the well, and then a rod pump lifts it. Today, two
decisions are made by experience: how much steam to inject, and how fast to run
the pump. Too little steam and the oil stays thick. Too much and diesel is
burned for nothing. And when the oil thickens again late in the cycle, the pump
rods start to float and can break. Our digital twin puts steam and pump into one
model and recommends both together. This is the live website.

## 0:25–0:55 · Overview page

The Overview is the one-page summary for a manager. On top, the key result:
steam per cubic metre of oil drops from 3.29 to 2.83, about 23 percent less
steam for the same oil. Next to it, diesel and CO₂ per cubic metre of oil. This
table compares the current cycle with the twin's recommended cycle, setting by
setting. Here you can put your own prices: diesel rate, discount, oil
realisation. Every number updates. And this "How these numbers are calculated"
link opens the working, nothing is hidden. Also, the whole site works in Hindi
with one click.

## 0:55–1:40 · Simulator page

The Simulator is where an engineer plays with one well. Six set-points: steam
volume, soak period, economic cutoff, pump speed, injection pressure and stroke
length. This selector is important: it decides what to do when the rods start
floating — pull the rods, slow the pump to hold the limit, or slow first and
then pull. Press "Simulate cycle". The twin runs the whole cycle day by day:
reservoir temperature, viscosity, oil rate, rod load and water cut. "Play the
cycle" animates it. "Try high speed" shows what happens if you push the pump too
fast — the rod-float index crosses the limit. Below is the dynamometer card, the
pump's health signature, computed at surface and at the pump. And "Check a
measured card" lets the field engineer upload a real card from the well. The
twin tells them whether the pump is healthy, gassy, or the rods are floating.

## 1:40–2:15 · Recommendation page

The Recommendation page is the optimiser. One click searches thousands of
steam-and-pump combinations and picks the best plan. The result shows current
versus recommended for every setting, plus the operating rule. The constraint
report shows every safety limit and whether the plan stays inside it. This
section shows uncertainty: the range around every number, so nobody is promised
a single magic figure. And here is the comparison choice: judge the plan against
a baseline that slows the pump, pulls at the first alarm, or does nothing. The
engineer stays in control: "Stage set-points", confirm, and only then does it
go to the simulator. Every recommendation is logged with a timestamp.

## 2:15–2:45 · Model basis page

The Model basis page is for the technical reviewer. It explains, in plain
words, the four models behind the twin: heating, thick oil, inflow and the rod
pump. It shows validation — what is confirmed from Oil India's public data and
what is an assumption still to be checked with them. Most important, "Use your
own data": Oil India uploads its cycle records as a CSV, the twin re-fits
itself, and the recommendation updates. The field view below plans which of the
wells gets steam next when the generator is limited.

## 2:45–3:00 · Close (screen: back to Overview)

So: one well, simulated day by day. Steam and pump decided together. Every
assumption tagged, every number with a range, and the engineer always in
charge. Built for Baghewala, ready for Oil India's data.

---

Recording notes: the "Run optimiser" click is instant in the recording because
the job was pre-run on the local server (result cache); on the free-tier live
site it is served precomputed. Hindi toggle and "Try high speed" are the two
moments worth a 2–3 s pause.
