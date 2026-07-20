import React, { useState, useEffect } from 'react';
import { FileText, CheckCircle2, ChevronRight, BarChart3, Users, Zap, SearchCode } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function App() {
  const [activeSection, setActiveSection] = useState('slide-1');

  useEffect(() => {
    const handleScroll = () => {
      const sections = document.querySelectorAll('section');
      let currentId = 'slide-1';
      sections.forEach((section) => {
        const sectionTop = section.offsetTop;
        if (window.scrollY >= sectionTop - 150) {
          currentId = section.getAttribute('id') || 'slide-1';
        }
      });
      setActiveSection(currentId);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      window.scrollTo({
        top: el.offsetTop - 80,
        behavior: 'smooth'
      });
    }
  };

  const navItems = [
    { id: 'slide-1', title: 'Overview' },
    { id: 'slide-2', title: 'Prioritization Framework' },
    { id: 'slide-3', title: 'Architecture Pipeline' },
    { id: 'slide-4', title: 'POC Demo' },
    { id: 'slide-5', title: 'Cortex Plan' },
    { id: 'slide-6', title: 'Evaluation' },
    { id: 'slide-7', title: 'Success Metrics' },
    { id: 'slide-8', title: 'Adoption Plan' },
    { id: 'slide-9', title: 'Next Steps' },
    { id: 'slide-10', title: 'Summary' }
  ];

  return (
    <div className="min-h-screen flex flex-col md:flex-row max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 bg-background font-sans">
      
      {/* Sidebar Navigation */}
      <nav className="w-full md:w-64 pt-12 pb-8 md:py-24 shrink-0 relative">
        <div className="md:sticky md:top-24 space-y-8">
          <div>
            <h2 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-2">Email Production Agent</h2>
            <p className="text-sm text-muted">A few hours of work — here's what I built</p>
          </div>
          
          <ul className="space-y-1 hidden md:block">
            {navItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => scrollTo(item.id)}
                  className={cn(
                    "text-sm w-full text-left py-2 px-3 rounded-md transition-colors",
                    activeSection === item.id 
                      ? "bg-surface font-medium text-foreground shadow-sm border border-border/50" 
                      : "text-muted hover:text-foreground hover:bg-surface/50"
                  )}
                >
                  {item.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 max-w-3xl md:ml-12 pt-8 md:pt-24 pb-32 space-y-32">
        
        {/* Slide 1 */}
        <section id="slide-1" className="scroll-mt-24 space-y-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-accent-blue/10 text-accent-blue rounded-full text-xs font-semibold uppercase tracking-wider mb-4">
            <span>A few hours of work</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-foreground leading-tight">
            What I Built for the Email Production Problem
          </h1>
          <p className="text-xl text-muted leading-relaxed max-w-2xl">
            From 2-week SLA to same-day turnaround — a working agent that turns a brief into a ready-to-review email.
          </p>
        </section>

        {/* Slide 2 */}
        <section id="slide-2" className="scroll-mt-24 space-y-8">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">The Prioritization Framework</h2>
            <p className="text-lg text-muted">Which problem to tackle first? It depends on what you optimize for.</p>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 text-center">
            {[
              { label: 'Hours', desc: 'Engineering + marketer hours saved per year', color: 'bg-amber-50 text-amber-700 border-amber-200' },
              { label: 'Revenue', desc: 'Revenue impact from faster campaigns, more volume', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
              { label: 'Reach', desc: '% of marketing org that directly benefits', color: 'bg-blue-50 text-blue-700 border-blue-200' },
              { label: 'Feasibility', desc: 'Technical + organizational difficulty to ship (inverted)', color: 'bg-violet-50 text-violet-700 border-violet-200' },
              { label: 'Data Readiness', desc: 'Are guidelines, templates, and data sources ready?', color: 'bg-rose-50 text-rose-700 border-rose-200' },
            ].map(d => (
              <div key={d.label} className={cn("rounded-lg border p-3", d.color)}>
                <div className="text-xs font-bold uppercase tracking-wider">{d.label}</div>
                <div className="text-[10px] leading-tight mt-1 opacity-70">{d.desc}</div>
              </div>
            ))}
          </div>
          
          <div className="bg-surface rounded-xl border border-border overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-border bg-background/50">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">Opportunity Scoring</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-surface text-muted text-xs uppercase tracking-wider border-b border-border">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Story</th>
                    <th className="px-6 py-4 font-semibold">Hours</th>
                    <th className="px-6 py-4 font-semibold">Rev</th>
                    <th className="px-6 py-4 font-semibold">Reach</th>
                    <th className="px-6 py-4 font-semibold">Feas.</th>
                    <th className="px-6 py-4 font-semibold">Data</th>
                    <th className="px-6 py-4 font-semibold text-accent-blue">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  <tr className="hover:bg-background/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-foreground">① Content Localization</td>
                    <td className="px-6 py-4">8/10</td><td className="px-6 py-4">8/10</td><td className="px-6 py-4">7/10</td><td className="px-6 py-4">3/10</td><td className="px-6 py-4">5/10</td><td className="px-6 py-4 font-medium">6.6</td>
                  </tr>
                  <tr className="hover:bg-background/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-foreground">② ABM Landing Pages</td>
                    <td className="px-6 py-4">7/10</td><td className="px-6 py-4">9/10</td><td className="px-6 py-4">5/10</td><td className="px-6 py-4">7/10</td><td className="px-6 py-4">7/10</td><td className="px-6 py-4 font-medium">7.0</td>
                  </tr>
                  <tr className="bg-accent-blue/5 hover:bg-accent-blue/10 transition-colors border-l-2 border-l-accent-blue">
                    <td className="px-6 py-4 font-semibold text-accent-blue flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      ③ Email Production
                    </td>
                    <td className="px-6 py-4 font-medium">10/10</td><td className="px-6 py-4 font-medium">8/10</td><td className="px-6 py-4 font-medium">9/10</td><td className="px-6 py-4 font-medium">8/10</td><td className="px-6 py-4 font-medium">9/10</td><td className="px-6 py-4 font-bold text-accent-blue">8.9</td>
                  </tr>
                  <tr className="hover:bg-background/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-foreground">④ Living Personas</td>
                    <td className="px-6 py-4">5/10</td><td className="px-6 py-4">4/10</td><td className="px-6 py-4">6/10</td><td className="px-6 py-4">5/10</td><td className="px-6 py-4">4/10</td><td className="px-6 py-4 font-medium">4.9</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
            <div className="space-y-3">
              <h4 className="font-semibold text-foreground flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-blue" /> Why email won</h4>
              <ul className="text-sm text-muted space-y-2 list-none">
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> Highest hours-saved ceiling (960-1,440 hrs/yr)</li>
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> Touches nearly every marketer who sends email</li>
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> Killing the 2-week SLA unlocks revenue beyond just efficiency</li>
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> The data I need (guidelines, templates) already exists</li>
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> Fastest path to an agent that's live, adopted, and measurable</li>
              </ul>
            </div>
            <div className="space-y-3">
              <h4 className="font-semibold text-foreground flex items-center gap-2"><SearchCode className="w-4 h-4 text-muted" /> What I deprioritized</h4>
              <ul className="text-sm text-muted space-y-2 list-none">
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> <strong>Localization:</strong> too many asset types for v1.</li>
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> <strong>ABM pages:</strong> strong #2. Brand validation module is directly reusable later.</li>
                <li className="flex items-start gap-2"><span className="text-border mt-0.5">•</span> <strong>Personas:</strong> highest technical risk, hardest to measure.</li>
              </ul>
            </div>
          </div>
          
          <div className="bg-surface p-4 rounded-lg border border-border text-sm flex gap-3 items-start">
            <div className="p-2 bg-orange-100 text-orange-600 rounded-md shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <span className="font-semibold text-foreground">What I'm least sure about:</span>
              <span className="text-muted ml-1">That brand guidelines are current. If they're 6 months stale, the agent generates outdated email. I'd validate this in week 1.</span>
            </div>
          </div>
        </section>

        {/* Slide 3 */}
        <section id="slide-3" className="scroll-mt-24 space-y-8">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">Architecture — The Pipeline</h2>
            <p className="text-lg text-muted">Five discrete steps. The LLM only touches what genuinely needs judgment.</p>
          </div>

          <div className="bg-surface border border-border rounded-xl p-8 font-mono text-sm overflow-x-auto whitespace-pre">
            <div className="flex items-center text-muted">
              <div className="flex flex-col items-center">
                <div className="bg-background px-3 py-1.5 rounded-md border border-border text-foreground font-semibold">BRIEF INTAKE</div>
                <div className="text-xs mt-1 text-muted">(code)</div>
              </div>
              <ChevronRight className="w-4 h-4 mx-4" />
              <div className="flex flex-col items-center">
                <div className="bg-accent-purple/10 border-accent-purple/20 px-3 py-1.5 rounded-md border text-accent-purple font-semibold">GENERATE</div>
                <div className="text-xs mt-1 text-accent-purple/70">(DeepSeek)</div>
              </div>
              <ChevronRight className="w-4 h-4 mx-4" />
              <div className="flex flex-col items-center">
                <div className="bg-background px-3 py-1.5 rounded-md border border-border text-foreground font-semibold">BRAND CHECK</div>
                <div className="text-xs mt-1 text-muted">(code)</div>
              </div>
              <ChevronRight className="w-4 h-4 mx-4" />
              <div className="flex flex-col items-center">
                <div className="bg-background px-3 py-1.5 rounded-md border border-border text-foreground font-semibold">PREVIEW</div>
                <div className="text-xs mt-1 text-muted">(code)</div>
              </div>
              <ChevronRight className="w-4 h-4 mx-4" />
              <div className="flex flex-col items-center">
                <div className="bg-background px-3 py-1.5 rounded-md border border-border text-foreground font-semibold">SYNC</div>
                <div className="text-xs mt-1 text-muted">(API)</div>
              </div>
            </div>
            <div className="mt-6 flex justify-center ml-20 relative">
              <div className="w-0.5 h-6 bg-border absolute -top-4 left-[390px]"></div>
              <div className="bg-accent-blue text-white px-4 py-2 rounded-md font-sans text-xs uppercase tracking-wider font-semibold shadow-sm ml-[220px]">
                Human Review Gate
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">Where I draw the line — and why</h3>
            <div className="bg-surface rounded-xl border border-border divide-y divide-border">
              {[
                { step: 'Brief intake & validation', file: 'intake.py', type: 'Deterministic (Python)', why: "Schema validation. Fail fast with a specific error if brief is malformed — don't ask a model to guess. Freeform text parsed by DeepSeek Flash into structured fields." },
                { step: 'Email generation (copy + HTML)', file: 'generate.py', type: 'LLM (DeepSeek)', why: "LLM returns ~1KB of copy slots as JSON. Python assembles ~10KB of production HTML from 4 Figma reference templates. Model never touches HTML structure — only writes copy. Falls back to Claude if unavailable." },
                { step: 'Brand compliance check', file: 'brand_check.py', type: 'Deterministic (Python)', why: "16 rules from 4 sources: brand guidelines, voice & tone, production email analysis, and accessibility standards. Regex + structural checks. Runs in milliseconds — no API call." },
                { step: 'Preview rendering', file: 'preview.py', type: 'Deterministic (HTML)', why: "Renders email at 600px with brand report side-by-side. Desktop/mobile toggle. Human reviews and approves here — this is the gate." },
                { step: 'Sync to Customer.io', file: 'sync.py', type: 'Deterministic (API)', why: "REST API call to Design Studio. Creates the email in the actual ESP where QA and sending happen. The model never touches the API." }
              ].map((item, i) => (
                <div key={i} className="p-4 sm:p-5 flex flex-col sm:flex-row gap-4 hover:bg-background/50 transition-colors">
                  <div className="sm:w-1/3">
                    <div className="font-medium text-foreground text-sm mb-1">{item.step}</div>
                    <div className={cn("text-xs inline-flex px-2 py-0.5 rounded-md font-medium", item.type.includes('LLM') ? 'bg-accent-purple/10 text-accent-purple' : 'bg-background border border-border text-muted')}>{item.type}</div>
                    {item.file && <div className="text-[11px] text-muted mt-1 font-mono">{item.file}</div>}
                  </div>
                  <div className="sm:w-2/3 text-sm text-muted leading-relaxed">
                    {item.why}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Slide 4 */}
        <section id="slide-4" className="scroll-mt-24 space-y-6">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">POC Demo</h2>
            <p className="text-lg text-muted">Figma Email Agent</p>
          </div>
          
          <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
            <img 
              src="https://userimg-assets.customeriomail.com/images/client-env-226115/01KXZYMX0CEGC6RGSV7XA4081P.jpeg" 
              alt="Figma Email Agent screenshot" 
              className="w-full block"
            />
            <div className="p-5 space-y-3">
              <p className="text-sm text-muted leading-relaxed">
                The Figma Email Agent takes a brief and generates a fully-styled, brand-compliant email — copy, HTML, and subject lines — in under a minute. A human reviews and approves before anything sends.
              </p>
              <a 
                href="https://www.amccutcheon.com/figma" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm font-medium text-accent-blue hover:text-accent-blue/80 transition-colors"
              >
                Try it at amccutcheon.com/figma
                <ChevronRight className="w-4 h-4" />
              </a>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">Demo Flow</h3>
              <ol className="text-sm text-muted space-y-3 list-decimal list-inside marker:text-foreground/40">
                <li>Load a sample brief or paste freeform text</li>
                <li>Hit Generate — DeepSeek returns copy slots as JSON</li>
                <li>Python assembles production HTML from the slots</li>
                <li>Brand checker runs 13 deterministic rules</li>
                <li>Preview renders — human reviews and approves</li>
                <li>Sync pushes to Customer.io Design Studio</li>
              </ol>
            </div>
            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">What I left for later</h3>
              <ul className="text-sm text-muted space-y-3">
                <li className="flex gap-2"><span className="text-border">•</span> A/B subject line flow (prompt built, not wired in)</li>
                <li className="flex gap-2"><span className="text-border">•</span> Feedback loop (architecture ready, not built)</li>
                <li className="flex gap-2"><span className="text-border">•</span> Send-time optimization</li>
                <li className="flex gap-2"><span className="text-border">•</span> Visual regression testing (Litmus / Email on Acid)</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Slide 5 */}
        <section id="slide-5" className="scroll-mt-24 space-y-8">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">Cortex / Repo Plan</h2>
            <p className="text-lg text-muted">I'm treating this like a product — versioned, documented, built for reuse.</p>
          </div>

          <div className="bg-surface rounded-xl border border-border overflow-hidden">
             <div className="px-6 py-4 border-b border-border bg-background/50 flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">Reusability Matrix</h3>
            </div>
            <table className="w-full text-sm text-left">
              <thead className="bg-surface text-muted text-xs uppercase tracking-wider border-b border-border">
                <tr>
                  <th className="px-6 py-3 font-semibold">From email production</th>
                  <th className="px-6 py-3 font-semibold">Reusable as</th>
                  <th className="px-6 py-3 font-semibold">Next consumer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  { from: 'brand_check.py', as: 'brand-validator skill', next: 'ABM pages, ads, social' },
                  { from: 'brand-guidelines.md', as: 'Shared context', next: 'ALL content workflows' },
                  { from: 'voice-and-tone.md', as: 'Shared context', next: 'ALL content workflows' },
                  { from: 'intake.py pattern', as: 'Structural pattern', next: 'Any brief/request intake' },
                  { from: 'preview.py review gate', as: 'UX pattern', next: 'Any human-in-the-loop flow' },
                ].map((row, i) => (
                  <tr key={i} className="hover:bg-background/50 transition-colors">
                    <td className="px-6 py-3 font-mono text-xs text-foreground bg-background/30">{row.from}</td>
                    <td className="px-6 py-3 text-muted">{row.as}</td>
                    <td className="px-6 py-3 font-medium text-accent-blue">{row.next}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-background rounded-lg border border-border p-6 flex items-start gap-4">
            <Users className="w-5 h-5 text-accent-purple shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-foreground mb-2 text-sm">How someone else picks this up for ABM pages</h4>
              <p className="text-sm text-muted leading-relaxed mb-0">
                They don't rebuild brand validation. They don't re-define the voice. They fork the repo, import the shared context, write ONE new prompt for landing page generation, and ship.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 6 */}
        <section id="slide-6" className="scroll-mt-24 space-y-8">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">Evaluation & Reliability</h2>
            <p className="text-lg text-muted">Measurement isn't optional — it's how I know what to retire.</p>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">Three Failure Modes</h3>
            <div className="grid gap-4">
              {[
                { mode: 'Bad brief', context: '(structured input error)', how: 'Deterministic validation in intake', result: 'Fails fast with a specific error. "I need these fields: audience, goal, CTA." Doesn\'t call the LLM.', color: 'border-l-orange-500' },
                { mode: 'Low-confidence output', context: '', how: 'LLM self-assesses 1-5 confidence score', result: 'Score ≤ 3 → preview shows ⚠ flag. Human decides.', color: 'border-l-yellow-500' },
                { mode: 'Brand violation', context: '(silent failure)', how: 'Deterministic brand checker runs on every output', result: 'Critical violations block sync. Warnings shown in preview. Human approves or rejects.', color: 'border-l-red-500' }
              ].map((item, i) => (
                <div key={i} className={cn("bg-surface border border-border rounded-lg p-5 flex flex-col md:flex-row gap-4 border-l-4", item.color)}>
                  <div className="md:w-1/3">
                    <div className="font-semibold text-foreground text-sm">{item.mode}</div>
                    {item.context && <div className="text-xs text-muted mt-0.5">{item.context}</div>}
                  </div>
                  <div className="md:w-1/3">
                    <div className="text-xs uppercase text-muted tracking-wider mb-1 font-semibold">How I catch it</div>
                    <div className="text-sm text-muted">{item.how}</div>
                  </div>
                  <div className="md:w-1/3">
                    <div className="text-xs uppercase text-muted tracking-wider mb-1 font-semibold">What happens</div>
                    <div className="text-sm text-foreground">{item.result}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">Brand Rule Sources (16 rules, 0 API calls)</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                { source: 'Figma brand guidelines', rules: 'Color palette (27 hex values), font stack (Whyte/Inter/Helvetica Neue), logo → figma.com link' },
                { source: 'Figma voice & tone', rules: '8 forbidden phrases ("game-changing", "revolutionary"), exclamation mark limit (≤2), all-caps body detection' },
                { source: 'Production email analysis', rules: 'CTA color validation (#5551FF lifecycle, #000000 newsletter), alt text on every image, unsubscribe required' },
                { source: 'Email accessibility (EMC 2026)', rules: 'Heading hierarchy (single h1, no skips), table role="presentation", descriptive link text, title tag, lang attribute' },
              ].map((s, i) => (
                <div key={i} className="bg-surface border border-border rounded-lg p-4">
                  <div className="text-xs font-semibold text-foreground mb-2">{s.source}</div>
                  <div className="text-xs text-muted leading-relaxed">{s.rules}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Slide 7 */}
        <section id="slide-7" className="scroll-mt-24 space-y-8">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">Success Metrics</h2>
            <p className="text-lg text-muted">Hours saved and revenue driven — measured, not asserted.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted flex items-center gap-2"><BarChart3 className="w-4 h-4" /> Today</h3>
              <div className="bg-surface rounded-lg border border-border p-5 space-y-4">
                <div className="flex justify-between items-baseline border-b border-border pb-3">
                  <span className="text-sm text-muted">Email turnaround SLA</span>
                  <span className="font-mono text-foreground font-medium">14 days</span>
                </div>
                <div className="flex justify-between items-baseline border-b border-border pb-3">
                  <span className="text-sm text-muted">Build time per email</span>
                  <span className="font-mono text-foreground font-medium">2 hours</span>
                </div>
                <div className="flex justify-between items-baseline border-b border-border pb-3">
                  <span className="text-sm text-muted">Revision rounds</span>
                  <span className="font-mono text-foreground font-medium">2-3</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span className="text-sm text-muted">Emails per month</span>
                  <span className="font-mono text-foreground font-medium">40-60</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-accent-blue flex items-center gap-2"><Zap className="w-4 h-4" /> With the agent</h3>
              <div className="bg-accent-blue/5 rounded-lg border border-accent-blue/20 p-5 space-y-4">
                <div className="flex justify-between items-baseline border-b border-accent-blue/10 pb-3">
                  <span className="text-sm text-foreground font-medium">Brief → QA</span>
                  <span className="font-mono text-accent-blue font-bold">&lt;1 hour</span>
                </div>
                <div className="flex justify-between items-baseline border-b border-accent-blue/10 pb-3">
                  <span className="text-sm text-foreground font-medium">Marketer time</span>
                  <span className="font-mono text-accent-blue font-bold">15 min</span>
                </div>
                <div className="flex justify-between items-baseline border-b border-accent-blue/10 pb-3">
                  <span className="text-sm text-foreground font-medium">Revision rounds</span>
                  <span className="font-mono text-accent-blue font-bold">0-1</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span className="text-sm text-foreground font-medium">Brand compliance</span>
                  <span className="font-mono text-accent-blue font-bold">100%</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4">
             <div className="bg-surface rounded-xl border border-border p-6 shadow-sm relative overflow-hidden">
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-green-500/10 rounded-full blur-2xl"></div>
                <h4 className="font-semibold text-foreground mb-4 text-lg">Hours Saved</h4>
                <ul className="text-sm text-muted space-y-3">
                  <li className="flex justify-between"><span className="text-foreground font-medium">Per email</span> <span>1.75 hours</span></li>
                  <li className="flex justify-between"><span className="text-foreground font-medium">Per month</span> <span>87.5 hours</span></li>
                  <li className="flex justify-between text-base font-semibold pt-2 border-t border-border mt-2"><span className="text-foreground">Per year</span> <span className="text-green-600">~1,050 hours — about half an FTE</span></li>
                </ul>
             </div>
             
             <div className="bg-surface rounded-xl border border-border p-6 shadow-sm relative overflow-hidden">
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-accent-blue/10 rounded-full blur-2xl"></div>
                <h4 className="font-semibold text-foreground mb-4 text-lg">Revenue Impact</h4>
                <ul className="text-sm text-muted space-y-3">
                  <li><span className="text-foreground font-medium">More volume:</span> No SLA means more campaigns ship</li>
                  <li><span className="text-foreground font-medium">Faster testing:</span> A/B tests ship in days, not weeks</li>
                  <li className="pt-2 border-t border-border mt-2 text-xs leading-relaxed">Measured via Customer.io send volume and attributed conversions — 6 months pre vs. post.</li>
                </ul>
             </div>
          </div>
        </section>

        {/* Slide 8 */}
        <section id="slide-8" className="scroll-mt-24 space-y-6">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">Adoption Plan</h2>
            <p className="text-lg text-muted">Shipping the agent is 50% of the work. Making marketers use it is the other 50%.</p>
          </div>

          <div className="grid gap-4">
             <div className="flex group">
               <div className="w-16 shrink-0 flex flex-col items-center">
                 <div className="w-8 h-8 rounded-full bg-accent-blue/10 text-accent-blue flex items-center justify-center font-bold text-sm">1-2</div>
                 <div className="w-px h-full bg-border group-last:bg-transparent mt-2"></div>
               </div>
               <div className="pb-8 pt-1">
                 <h4 className="font-semibold text-foreground mb-2">Pilot with one person</h4>
                 <p className="text-sm text-muted leading-relaxed">Find whoever feels the 2-week SLA most. Walk through THEIR actual next email — not a demo. Goal: one email shipped through the agent with zero hand-holding.</p>
               </div>
             </div>

             <div className="flex group">
               <div className="w-16 shrink-0 flex flex-col items-center">
                 <div className="w-8 h-8 rounded-full bg-surface border border-border text-muted flex items-center justify-center font-bold text-sm">3-4</div>
                 <div className="w-px h-full bg-border group-last:bg-transparent mt-2"></div>
               </div>
               <div className="pb-8 pt-1">
                 <h4 className="font-semibold text-foreground mb-2">Expand to the team</h4>
                 <p className="text-sm text-muted leading-relaxed">That first person is your champion. "I built an email in 15 minutes." Group walkthrough with real briefs from the backlog. Goal: 5+ emails through the agent.</p>
               </div>
             </div>

             <div className="flex group">
               <div className="w-16 shrink-0 flex flex-col items-center">
                 <div className="w-8 h-8 rounded-full bg-surface border border-border text-muted flex items-center justify-center font-bold text-sm">5-8</div>
                 <div className="w-px h-full bg-border group-last:bg-transparent mt-2"></div>
               </div>
               <div className="pb-8 pt-1">
                 <h4 className="font-semibold text-foreground mb-2">Open to everyone</h4>
                 <p className="text-sm text-muted leading-relaxed">Brief intake form goes live. Any marketer can submit. Email team does final QA only. Goal: 50% of monthly volume through the agent.</p>
               </div>
             </div>
          </div>
        </section>

        {/* Slide 9 */}
        <section id="slide-9" className="scroll-mt-24 space-y-8">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground mb-3">What I'd Do Next</h2>
            <p className="text-lg text-muted">The first agent is the hardest. The second one takes half the time.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-surface border border-border rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-muted mb-4">Immediate (2 Wks)</h4>
              <ul className="text-sm text-muted space-y-3 list-none">
                <li className="flex gap-2"><span className="text-accent-blue">•</span> Validate brand guidelines freshness</li>
                <li className="flex gap-2"><span className="text-accent-blue">•</span> Add human annotation feedback loop</li>
                <li className="flex gap-2"><span className="text-accent-blue">•</span> Add visual regression testing</li>
              </ul>
            </div>
            <div className="bg-surface border border-border rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-muted mb-4">Next agent on deck</h4>
              <p className="font-medium text-foreground text-sm mb-3">ABM Landing Pages</p>
              <p className="text-xs text-muted leading-relaxed">
                Brand validation, review gate, and eval framework are already reusable. Build time drops from 3-4 weeks to maybe 1.
              </p>
            </div>
            <div className="bg-surface border border-border rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow bg-gradient-to-br from-background to-accent-blue/5">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-muted mb-4">Where this goes</h4>
              <p className="text-xs text-muted leading-relaxed">
                Each new agent adds to the shared cortex instead of being its own silo. The goal isn't 10 agents — it's a system where building the 11th takes an afternoon.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 10 */}
        <section id="slide-10" className="scroll-mt-24">
          <div className="bg-zinc-900 text-zinc-100 rounded-2xl p-8 md:p-12 relative overflow-hidden shadow-xl">
            <div className="absolute top-0 right-0 w-64 h-64 bg-accent-blue/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
            
            <h2 className="text-3xl font-semibold tracking-tight mb-8">Thank you!</h2>
            
            <div className="space-y-6 text-zinc-300">
              <div className="border-l-2 border-accent-blue pl-4">
                <p className="text-lg font-medium text-white mb-2">This was a fun assignment that I enjoyed thinking through and hope that you've enjoyed learning about it.</p>
              </div>
            </div>
          </div>
        </section>
        
      </main>
    </div>
  );
}