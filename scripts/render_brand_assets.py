#!/usr/bin/env python3
"""Render the profile's original, self-contained SVG artwork.

Uses only the Python standard library. Run from any directory with:
    python3 scripts/render_brand_assets.py
"""

from dataclasses import dataclass
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BG = "#0b1018"
PANEL = "#111a26"
EDGE = "#253245"
LIME = "#c7f284"
BLUE = "#88d8ff"
LAVENDER = "#b7a3ff"
WHITE = "#edf3fa"
MUTED = "#9baabe"


def text(x, y, content, *, size=16, fill=WHITE, weight=400, family="sans", extra=""):
    return (
        f'<text x="{x}" y="{y}" class="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" {extra}>{escape(content)}</text>'
    )


def svg(width, height, title, description, body, accent=LIME):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">{escape(description)}</desc>
  <defs>
    <linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="{PANEL}"/>
      <stop offset="1" stop-color="{BG}"/>
    </linearGradient>
    <radialGradient id="halo">
      <stop stop-color="{accent}" stop-opacity=".13"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="{EDGE}" stroke-width=".65"/>
    </pattern>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }}
    .mono {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }}
    .trace {{ animation: trace 18s linear infinite; }}
    .pulse {{ animation: pulse 5s ease-in-out infinite; }}
    .cursor {{ animation: cursor 2.4s steps(2, jump-none) infinite; }}
    @keyframes trace {{ to {{ stroke-dashoffset: -96; }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .4; }} 50% {{ opacity: 1; }} }}
    @keyframes cursor {{ 0%, 65% {{ opacity: 1; }} 100% {{ opacity: .25; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .trace, .pulse, .cursor {{ animation: none !important; }}
    }}
  </style>
  <rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="22" fill="url(#surface)" stroke="{EDGE}"/>
{body}
</svg>
'''


def orbital(cx, cy, scale=1, *, labels=True):
    """A circuit-like orbit connecting exploration, building, and shipping."""
    captions = ''.join((
        text(-127, -88, 'EXPLORE', size=9, fill=MUTED, family='mono'),
        text(81, -84, 'BUILD', size=9, fill=MUTED, family='mono'),
        text(84, 98, 'SHIP', size=9, fill=MUTED, family='mono'),
    )) if labels else ''
    return f'''<g transform="translate({cx} {cy}) scale({scale})">
    <circle r="169" fill="url(#halo)"/>
    <circle r="127" stroke="{EDGE}" fill="none"/>
    <circle r="102" stroke="{EDGE}" fill="none" stroke-dasharray="2 9"/>
    <path d="M-150 0H150 M0-150V150" stroke="{EDGE}" stroke-dasharray="3 8"/>
    <ellipse rx="145" ry="56" transform="rotate(-34)" stroke="{LIME}" stroke-opacity=".28" fill="none"/>
    <ellipse rx="145" ry="56" transform="rotate(34)" stroke="{BLUE}" stroke-opacity=".34" fill="none"/>
    <ellipse class="trace" rx="145" ry="56" transform="rotate(-34)" stroke="{LIME}" stroke-width="1.3" stroke-dasharray="12 84" fill="none"/>
    <path d="M-120-71H-72L-44-43 M115-67H73L44-38 M-110 87H-73L-42 45 M115 73H73L43 43" stroke="{EDGE}" stroke-width="1.5" fill="none"/>
    <rect x="-47" y="-47" width="94" height="94" rx="20" fill="{BG}" stroke="{LIME}" stroke-opacity=".45"/>
    <rect x="-38" y="-38" width="76" height="76" rx="13" fill="{PANEL}" stroke="{EDGE}"/>
    <path d="M-13-13L-26 0L-13 13 M13-13L26 0L13 13 M5-19L-5 19" stroke="{LIME}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <g stroke="{EDGE}" stroke-width="2">
      <path d="M-23-56V-47 M0-56V-47 M23-56V-47 M-23 47V56 M0 47V56 M23 47V56 M-56-23H-47 M-56 0H-47 M-56 23H-47 M47-23H56 M47 0H56 M47 23H56"/>
    </g>
    <circle cx="-120" cy="-71" r="6" fill="{BG}" stroke="{LIME}" stroke-width="2"/>
    <circle cx="115" cy="-67" r="5" fill="{BG}" stroke="{BLUE}" stroke-width="2"/>
    <circle cx="-110" cy="87" r="5" fill="{BG}" stroke="{LAVENDER}" stroke-width="2"/>
    <circle cx="115" cy="73" r="6" fill="{BG}" stroke="{LIME}" stroke-width="2"/>
    <circle class="pulse" cx="115" cy="73" r="11" fill="none" stroke="{LIME}" stroke-opacity=".3"/>
    {captions}
  </g>'''


def hero():
    body = f'''  <rect x="721" y="24" width="353" height="268" rx="16" fill="url(#grid)" opacity=".5"/>
  <path d="M48 88H656" stroke="{EDGE}"/>
  <rect x="48" y="47" width="8" height="8" rx="2" fill="{LIME}"/>
  {text(69, 57, 'SRISHANTH GOUD', size=15, weight=650, extra='letter-spacing="1.5"')}
  {text(263, 57, '/ @iamsrishanth', size=13, fill=MUTED, family='mono')}
  {text(48, 163, 'Curiosity in.', size=58, weight=650, extra='letter-spacing="-2"')}
  {text(48, 227, 'Working software out.', size=54, fill=LIME, weight=650, extra='letter-spacing="-2"')}
  {text(50, 270, 'AI tools · web products · Android experiments', size=18, fill=MUTED)}
  {orbital(888, 167, .85)}
  <path d="M48 311H1052" stroke="{EDGE}"/>
  {text(48, 348, '>', size=18, fill=LIME, family='mono')}
  {text(72, 348, 'build · ship · repeat', size=15, family='mono')}
  <rect class="cursor" x="274" y="333" width="8" height="18" rx="1" fill="{LIME}"/>
  {text(1052, 348, 'IDEAS BECOME INTERFACES', size=11, fill=MUTED, family='mono', extra='text-anchor="end" letter-spacing="1.4"')}
'''
    return svg(1100, 390, 'Srishanth Goud — curiosity in, working software out.',
               'A dark engineering workspace with lime typography and a softly animated circuit orbit. AI tools, web products, and Android experiments. Build, ship, repeat.', body)


def hero_mobile():
    body = f'''  <rect x="226" y="25" width="188" height="125" rx="14" fill="url(#grid)" opacity=".4"/>
  {orbital(345, 82, .30, labels=False)}
  <rect x="28" y="35" width="7" height="7" rx="2" fill="{LIME}"/>
  {text(45, 45, 'SRISHANTH GOUD', size=14, weight=650, extra='letter-spacing="1"')}
  {text(28, 70, '@iamsrishanth', size=13, fill=MUTED, family='mono')}
  <path d="M28 129H412" stroke="{EDGE}"/>
  {text(28, 183, 'Curiosity in.', size=44, weight=650, extra='letter-spacing="-1.6"')}
  {text(28, 233, 'Working software', size=39, fill=LIME, weight=650, extra='letter-spacing="-1.5"')}
  {text(28, 278, 'out.', size=44, fill=LIME, weight=650, extra='letter-spacing="-1.6"')}
  {text(28, 315, 'AI tools · web products', size=16, fill=MUTED)}
  {text(28, 338, 'Android experiments', size=16, fill=MUTED)}
  <path d="M28 358H412" stroke="{EDGE}"/>
  {text(28, 389, '> build · ship · repeat', size=14, family='mono')}
  <rect class="cursor" x="234" y="376" width="7" height="16" rx="1" fill="{LIME}"/>
'''
    return svg(440, 420, 'Srishanth Goud — curiosity in, working software out.',
               'AI tools, web products, and Android experiments. A compact engineering-inspired profile banner with a circuit orbit. Build, ship, repeat.', body)


@dataclass(frozen=True)
class Card:
    key: str
    number: str
    category: str
    title: str
    subtitle: tuple[str, ...]
    stack: str
    accent: str


CARDS = (
    Card('crm', '01', 'SYSTEMS', 'OpenTeleCRM', ('Self-hosted CRM.',), 'NestJS · Next.js · PostgreSQL', LIME),
    Card('mcp', '02', 'AI + AUTOMATION', 'meta-ads-mcp', ('Connect agents to Meta Ads.',), 'Python · MCP · httpx', BLUE),
    Card('drivetv', '03', 'ANDROID', 'DriveTV', ('Google Drive on the big screen.',), 'Kotlin · Compose · Media3', LAVENDER),
    Card('web', '04', 'WEB', 'La Sabroso', ('A cafe website with', 'a Next.js foundation.'), 'Next.js · TypeScript · Tailwind', LIME),
)


def card_icon(card):
    a = card.accent
    frame = f'''<g transform="translate(427 111)">
      <circle r="59" fill="url(#halo)"/>
      <rect x="-43" y="-43" width="86" height="86" rx="20" fill="{PANEL}" stroke="{EDGE}"/>
    '''
    if card.key == 'crm':
        icon = f'''<g fill="{BG}" stroke="{a}" stroke-width="1.5">
          <rect x="-15" y="-27" width="30" height="20" rx="5"/>
          <rect x="-28" y="12" width="21" height="17" rx="4"/>
          <rect x="7" y="12" width="21" height="17" rx="4"/>
          <path d="M0-7V3 M-17 12V3H17V12" fill="none"/>
        </g>
        <path d="M-7-17H7 M-22 20H-13 M13 20H22" stroke="{a}" stroke-opacity=".6" stroke-linecap="round"/>
        '''
    elif card.key == 'mcp':
        icon = f'''<path d="M-27-18H-12L0-3 M27-18H12L0-3 M0 8V27" stroke="{a}" stroke-width="1.5" fill="none"/>
        <g fill="{BG}" stroke="{a}" stroke-width="1.5">
          <rect x="-32" y="-25" width="14" height="14" rx="4"/>
          <rect x="18" y="-25" width="14" height="14" rx="4"/>
          <rect x="-8" y="-8" width="16" height="16" rx="5"/>
          <rect x="-8" y="21" width="16" height="12" rx="3"/>
        </g>
        <circle class="pulse" r="2" fill="{a}"/>
        '''
    elif card.key == 'drivetv':
        icon = f'''<rect x="-29" y="-22" width="58" height="39" rx="7" fill="{BG}" stroke="{a}" stroke-width="1.5"/>
        <path d="M-12 25H12 M0 17V25" stroke="{a}" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M-5-12L10-3L-5 6Z" fill="{a}"/>
        <circle cx="22" cy="11" r="1.5" fill="{a}" opacity=".6"/>
        '''
    else:
        icon = f'''<path d="M-22-5H14V6A16 16 0 0 1-2 22H-6A16 16 0 0 1-22 6Z" fill="{BG}" stroke="{a}" stroke-width="1.5"/>
        <path d="M14-1H20A8 8 0 0 1 20 15H11 M-25 28H20" fill="none" stroke="{a}" stroke-width="1.5" stroke-linecap="round"/>
        <path class="pulse" d="M-12-15C-20-23-4-23-12-31 M0-15C-8-23 8-23 0-31" fill="none" stroke="{a}" stroke-width="1.5" stroke-linecap="round"/>
        '''
    return frame + icon + '</g>'


def project_card(card):
    subtitle = '\n'.join(text(28, 126 + (i * 22), line, size=17, fill=MUTED)
                         for i, line in enumerate(card.subtitle))
    body = f'''  <path d="M28 21H72" stroke="{card.accent}" stroke-width="2" stroke-linecap="round"/>
  {text(28, 49, card.number, size=12, fill=card.accent, family='mono')}
  {text(60, 49, '/ ' + card.category, size=11, fill=MUTED, family='mono', extra='letter-spacing="1.5"')}
  <path d="M476 34H490V48 M490 34L476 48" stroke="{card.accent}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  {text(28, 97, card.title, size=33, weight=650, extra='letter-spacing="-.7"')}
  {subtitle}
  {text(28, 180, card.stack, size=12, fill=card.accent, family='mono')}
  {card_icon(card)}
  <path d="M28 203H492" stroke="{EDGE}"/>
  {text(28, 229, 'EXPLORE REPOSITORY', size=10, fill=MUTED, family='mono', extra='letter-spacing="1.7"')}
  <path d="M465 225H491 M485 219L491 225L485 231" stroke="{card.accent}" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
'''
    description = f'{card.category}. {" ".join(card.subtitle)} Built with {card.stack}. Explore the repository.'
    return svg(520, 250, card.title, description, body, accent=card.accent)


def footer():
    body = f'''  <rect x="31" y="29" width="30" height="30" rx="8" fill="{BG}" stroke="{EDGE}"/>
  <path d="M40 38L46 44L40 50 M48 50H53" stroke="{LIME}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  {text(80, 51, 'End of file. Start a conversation.', size=21, weight=500)}
  <path d="M466 44H966" stroke="{EDGE}" stroke-dasharray="2 7"/>
  {text(1009, 50, '>', size=20, fill=LIME, family='mono')}
  <rect class="cursor" x="1037" y="32" width="11" height="23" rx="1" fill="{LIME}"/>
'''
    return svg(1100, 90, 'End of file. Start a conversation.',
               'A terminal prompt and a softly blinking lime cursor invite a conversation.', body)


def main():
    ASSETS.mkdir(exist_ok=True)
    outputs = {'hero.svg': hero(), 'hero-mobile.svg': hero_mobile(), 'footer.svg': footer()}
    outputs.update({f'project-{card.key}.svg': project_card(card) for card in CARDS})
    for name, markup in outputs.items():
        ET.fromstring(markup)
        (ASSETS / name).write_text(markup, encoding='utf-8')
        print(f'Rendered assets/{name}')


if __name__ == '__main__':
    main()
