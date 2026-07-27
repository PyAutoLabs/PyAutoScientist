# PyAutoScientist

**A working reference implementation of a human-led AI software-development organism.**

PyAutoScientist is the live system that develops all of the [PyAutoLabs](https://github.com/PyAutoLabs)
software. Plain-English intent becomes tested, released code through an organism of
repositories — a set of AI agents that plan, implement, test and release the work, with a
human directing it and checkpointing every decision that matters. It is not a framework you
install; it is documented so you can fork it and lead your own.

📖 **Docs:** https://pyautoscientist.readthedocs.io
🍴 **Adoption guide:** https://pyautoscientist.readthedocs.io/en/latest/adoption/guide.html

> This repo is a home for the PyAutoScientist docs and links for now. It will grow as the
> organism does.

## The organs

<!-- repos_sync:organs:begin -->
| Organ | Repo | Role |
|---|---|---|
| Mind | [PyAutoMind](https://github.com/PyAutoLabs/PyAutoMind) | Where you lead — every piece of work starts here as a plain-English markdown file saying *what* to do. |
| Brain | [PyAutoBrain](https://github.com/PyAutoLabs/PyAutoBrain) | The reasoning layer that works out *how* — classifying, planning and routing each task through specialist agents. |
| Hands | [PyAutoHands](https://github.com/PyAutoLabs/PyAutoHands) | The executor that packages, tags and releases the libraries to PyPI, nightly. |
| Heart | [PyAutoHeart](https://github.com/PyAutoLabs/PyAutoHeart) | The health monitor whose GREEN/YELLOW/RED verdict is the authoritative "is it safe to release?" gate. |
| Memory | [PyAutoMemory](https://github.com/PyAutoLabs/PyAutoMemory) | Long-term scientific knowledge — cross-linked literature wikis the agents consult. |
| Gut | [PyAutoGut](https://github.com/PyAutoLabs/PyAutoGut) | The storage mirror of Memory — holds *condemned* material (stale branches, dead code) as recoverable git refs, then voids it on a sweep. |
| Nerves | [PyAutoNerves](https://github.com/PyAutoLabs/PyAutoNerves) | The configuration and serialization layer (`autonerves`) connecting the organism's conventions to every library. |
<!-- repos_sync:organs:end -->

The software the organism develops lives across the [PyAutoLabs](https://github.com/PyAutoLabs)
organisation — see the [front door](https://pyautolabs.github.io) for the full map.

## Community

PyAutoScientist is the canonical home for community-wide PyAutoLabs policy.
Please read the [contribution guide](CONTRIBUTING.md) and
[Code of Conduct](CODE_OF_CONDUCT.md) before participating. The
[PyAuto AI Policy](AI_POLICY.md) explains how natural language and AI are used
responsibly across scientific analysis, learning, and software development.

## License

Released under the [MIT License](https://opensource.org/licenses/MIT). Copyright (c) 2026 Jammy2211.
