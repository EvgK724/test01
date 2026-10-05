CSS = r"""
  /* ——— Справочник: разделы, таблицы, калькуляторы */
  h2.algo-h{line-height:1.35}
  .algo,.lbl{scroll-margin-top:8px}
  .jump{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px}
  .jump button{min-height:44px;padding:0 14px;border-radius:999px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;cursor:pointer}
  .jump button:active{background:var(--raise)}
  .tt,.dz{margin-top:2px}
  .tr,.dr{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:12px;row-gap:2px;padding:10px 0;border-top:1px solid var(--line)}
  .tr:first-child,.dr:first-child{border-top:0}
  .tk,.dk{flex:0 1 auto;min-width:0;overflow-wrap:break-word;font-family:var(--serif);font-size:21px;line-height:1.2;color:var(--accent)}
  .tv{flex:0 1 auto;margin-left:auto;min-width:0;font-family:var(--serif);font-size:20px;line-height:1.2;color:var(--yes-text);text-align:right}
  .dv{flex:0 1 auto;margin-left:auto;min-width:0;font-family:var(--serif);font-size:20px;line-height:1.2;color:var(--text);text-align:right}
  .td,.dd{flex:1 0 100%;margin-top:1px;font-size:14px;line-height:1.45;color:var(--soft)}
  .algo-note + .algo-note{margin-top:6px}

  .calc{margin-top:14px;padding:12px 14px 14px;border-radius:16px;background:var(--bg);border:1px solid var(--line);display:flex;flex-direction:column;gap:6px}
  .calc-h{margin:0 0 2px;font-size:15px;font-weight:600;color:var(--text)}
  .calc-h small{display:block;margin-top:1px;font-size:13px;font-weight:400;color:var(--muted)}
  .fl{margin:6px 0 0;font-size:13px;font-weight:600;letter-spacing:.03em;color:var(--muted)}
  .fl small{margin-left:5px;font-size:12px;font-weight:400;letter-spacing:0}
  .inp{display:block;width:100%;min-height:48px;padding:0 12px;border-radius:12px;border:1px solid var(--line-2);background:var(--surface);color:var(--text);font:inherit;font-size:17px;font-variant-numeric:tabular-nums;-webkit-appearance:none;appearance:none}
  .inp::placeholder{color:var(--muted)}
  .inp:focus{outline:2px solid var(--accent);outline-offset:1px}
  .inp-row{display:grid;grid-template-columns:minmax(0,1fr);gap:6px}
  .inp-row.has-x{grid-template-columns:minmax(0,1fr) 48px}
  .x{min-height:48px;border-radius:12px;border:1px solid var(--line-2);background:transparent;color:var(--muted);font-size:20px;line-height:1;cursor:pointer}
  .seg{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
  .seg.s3{grid-template-columns:repeat(3,minmax(0,1fr))}
  .seg.s4{grid-template-columns:repeat(auto-fit,minmax(64px,1fr))}
  .seg.s4 .chip{font-size:14px}
  .chip{overflow-wrap:break-word}
  .err s,.err .good{min-width:0;overflow-wrap:break-word}
  .seg.s2{grid-template-columns:repeat(2,minmax(0,1fr))}
  .chip{min-height:44px;padding:0 2px;border-radius:12px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;line-height:1.2;cursor:pointer}
  .chip[aria-pressed="true"]{background:var(--raise);color:var(--text);border-color:var(--accent)}
  .flags{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
  .flags .chip{padding:6px 12px;text-align:left}
  .g2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 8px}
  .res{margin-top:8px;border-top:1px solid var(--line)}
  .rl{padding:10px 0;border-bottom:1px solid var(--line)}
  .rl:last-child{border-bottom:0;padding-bottom:0}
  .rk{margin:0;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--blue)}
  .rv{margin:2px 0 0;font-family:var(--serif);font-size:22px;line-height:1.25;color:var(--text);text-wrap:balance}
  .rn{margin:3px 0 0;font-size:14px;line-height:1.45;color:var(--muted)}
  .rl.warn .rv{color:var(--no-text)}
  .rl.ok .rv{color:var(--yes-text)}
  .pill{display:inline-block;margin-left:4px;padding:0 9px;border-radius:999px;font-size:12px;font-weight:600;line-height:20px;border:1px solid currentColor;white-space:nowrap;vertical-align:1px}
  .p-now{color:var(--yes-text);background:rgba(78,135,103,.14)}
  .p-wait{color:var(--blue);background:var(--blue-soft)}
  .p-late{color:var(--muted)}
  .crcl{margin:10px 0 0;font-size:15px;color:var(--soft)}
  .crcl b{margin:0 4px;font-family:var(--serif);font-weight:400;font-size:30px;line-height:1;color:var(--text);font-variant-numeric:tabular-nums}
  .dzr{list-style:none;margin:6px 0 0;padding:0}
  .dzr li{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:10px;row-gap:2px;padding:9px 0;border-top:1px solid var(--line)}
  .dzr .n{flex:0 1 auto;min-width:0;font-size:15px;font-weight:600;color:var(--soft)}
  .dzr .d{flex:0 1 auto;margin-left:auto;min-width:0;font-family:var(--serif);font-size:20px;line-height:1.2;color:var(--text);text-align:right}
  .dzr .d.low{color:var(--accent)}
  .dzr .d.no{color:var(--no-text)}
  .dzr .w{flex:1 0 100%;margin-top:0;font-size:13px;line-height:1.4;color:var(--muted)}
  .res-note{margin:8px 0 0;font-size:13px;line-height:1.45;color:var(--muted)}
  .q{overflow-wrap:break-word}
  .t-rule + .t-rule{margin-top:-4px}

  .lst{list-style:none;margin:0;padding:0}
  .lst li{padding:11px 14px 12px;border-top:1px solid var(--line)}
  .lst li:first-child{border-top:0}
  .sw-k{margin:0;font-family:var(--serif);font-size:20px;line-height:1.25;color:var(--accent)}
  .sw-v{margin:3px 0 0;font-size:16px;line-height:1.45;color:var(--text)}
  .sw-s{margin:3px 0 0;font-size:12px;font-weight:600;letter-spacing:.03em;color:var(--muted)}
  .ad-k{margin:0;font-size:14px;font-weight:600;line-height:1.35;color:var(--soft)}
  .ad-v{margin:2px 0 0;font-family:var(--serif);font-size:21px;line-height:1.25;color:var(--accent)}
  .ad-n{margin:3px 0 0;font-size:14px;line-height:1.45;color:var(--muted)}
  .iv-k{margin:0;font-size:14px;font-weight:600;line-height:1.35;color:var(--soft)}
  .iv-k span{font-weight:400;color:var(--muted)}
  .iv-v{margin:3px 0 0;font-family:var(--serif);font-size:19px;line-height:1.3}
  .iv-v::before{content:"";display:inline-block;width:9px;height:9px;margin-right:8px;border-radius:50%;background:currentColor;vertical-align:2px}
  .v-yes{color:var(--yes-text)}
  .v-maybe{color:#e5c07b}
  .v-no{color:var(--no-text)}
  .src{margin:0;padding:0 0 0 22px;font-size:13px;line-height:1.45;color:var(--soft)}
  .src li{margin:0 0 7px;padding-left:2px}
  .src a{color:var(--blue);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px;overflow-wrap:anywhere}
  .foot{margin:14px 0 6px;font-size:13px;line-height:1.45;color:var(--muted)}
  .r-title{font-size:min(40px,10vw);overflow-wrap:break-word;hyphens:auto}
  .t-title,.t-sub{overflow-wrap:break-word;hyphens:auto}
  .opt{min-width:0;overflow-wrap:break-word;hyphens:auto}
  label.fl{display:block}
  .fl small{margin-left:0}
  .abbr{margin:0 0 14px;padding:12px 14px 10px;border:1px solid var(--line);border-radius:16px}
  .abbr dl{margin:4px 0 0}
  .abbr dl div{display:grid;grid-template-columns:minmax(0,7.5em) minmax(0,1fr);column-gap:10px;padding:5px 0;border-top:1px solid var(--line)}
  .abbr dl div:first-child{border-top:0}
  .abbr dt{font-size:14px;font-weight:600;line-height:1.4;color:var(--text);overflow-wrap:break-word}
  .abbr dd{margin:0;font-size:14px;line-height:1.4;color:var(--soft);overflow-wrap:break-word}
  .mx-note{font-size:14px;color:var(--muted)}
"""
