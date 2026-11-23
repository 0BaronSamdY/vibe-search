import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

if 'image_url,vibe_attributes' in content and 'image_url,place_type,vibe_attributes' not in content:
    content = content.replace('image_url,vibe_attributes', 'image_url,place_type,vibe_attributes')
    changes += 1

if "placeType:'all'" not in content:
    content = content.replace("preset:null}", "preset:null,placeType:'all'}")
    changes += 1

if 'function getTypeIcon' not in content:
    funcs = """function getTypeIcon(type){return type==='cafe'?'☕':type==='bar'?'🍷':'🍽️'}
function getTypeName(type){return type==='cafe'?t('type_cafe'):type==='bar'?t('type_bar'):t('type_restaurant')}
"""
    content = content.replace('function setLanguage(l){', funcs + 'function setLanguage(l){')
    changes += 1

if 'function setType' not in content:
    code = """function setType(type){state.placeType=type;document.querySelectorAll('.type-btn').forEach(b=>b.classList.toggle('on',b.getAttribute('data-type')===type));applyFilters();}
"""
    content = content.replace('function setLanguage(l){', code + '\nfunction setLanguage(l){')
    changes += 1

if "state.placeType!=='all'" not in content:
    old = "if(state.favOnly&&!favs.has(p.id))return false;"
    new = "if(state.favOnly&&!favs.has(p.id))return false;\n    if(state.placeType!=='all'&&p.place_type!==state.placeType)return false;"
    content = content.replace(old, new)
    changes += 1

translations = [
    ('type_all:"Все"', 'type_all:"Все",type_cafe:"Кафе",type_bar:"Бары",type_restaurant:"Рестораны"'),
    ('type_all:"Tutti"', 'type_all:"Tutti",type_cafe:"Caffè",type_bar:"Bar",type_restaurant:"Ristoranti"'),
    ('type_all:"All"', 'type_all:"All",type_cafe:"Cafés",type_bar:"Bars",type_restaurant:"Restaurants"')
]
for old, new in translations:
    if old in content and new not in content:
        content = content.replace(old, new)

if 'class="type-filter"' not in content:
    html = """        <div class="type-filter">
          <button class="type-btn on" data-type="all" onclick="setType('all')">🏪 <span data-i18n="type_all">Все</span></button>
          <button class="type-btn" data-type="cafe" onclick="setType('cafe')">☕ <span data-i18n="type_cafe">Кафе</span></button>
          <button class="type-btn" data-type="bar" onclick="setType('bar')">🍷 <span data-i18n="type_bar">Бары</span></button>
          <button class="type-btn" data-type="restaurant" onclick="setType('restaurant')">🍽️ <span data-i18n="type_restaurant">Рестораны</span></button>
        </div>
"""
    content = content.replace('<div class="presets">', html + '        <div class="presets">')
    changes += 1

if '.type-filter{' not in content:
    css = """.type-filter{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:4px}
.type-btn{padding:8px 14px;border-radius:999px;border:1.5px solid var(--track);background:var(--cream);font-size:13px;font-weight:600;color:var(--muted);transition:all .2s}
.type-btn:hover{border-color:var(--ochre);color:var(--ochre)}.type-btn.on{background:var(--ochre);border-color:var(--ochre);color:var(--espresso)}
.type-badge{display:inline-block;padding:3px 8px;border-radius:6px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-left:8px}
.type-badge.cafe{background:#E9A13B;color:var(--espresso)}
.type-badge.bar{background:#7C2D3E;color:var(--paper)}
.type-badge.restaurant{background:#5F8F4E;color:var(--paper)}
"""
    content = content.replace('.presets{', css + '.presets{')
    changes += 1

if "state.placeType='all'" not in content:
    content = content.replace('state.preset=null;', "state.preset=null;state.placeType='all';")
    changes += 1

if "if(!p.place_type)p.place_type='cafe'" not in content:
    old = "return p;"
    new = "if(!p.place_type)p.place_type='cafe';\n      return p;"
    content = content.replace(old, new, 1)
    changes += 1

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Применено изменений: {changes}")
