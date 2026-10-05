# Профиль «плитка на экран Домой»: python3 mkprofile.py <папка> <ключ> <подпись> <url> <имя профиля> <описание>
import plistlib, uuid, pathlib, sys
folder, key, label, url, display, desc = sys.argv[1:7]
p = plistlib.loads(pathlib.Path("manage-tile.mobileconfig").read_bytes())
ref = plistlib.loads(pathlib.Path("countable-tile.mobileconfig").read_bytes())
clip = p["PayloadContent"][0]
clip["Icon"] = pathlib.Path(folder, "tile", "icon-400.png").read_bytes()
clip["Label"] = label
clip["PayloadDisplayName"] = label
clip["PayloadIdentifier"] = "personal.english.webclip." + key
clip["PayloadUUID"] = str(uuid.uuid4()).upper()
clip["URL"] = url
p["PayloadDescription"] = desc + " Удалить: Настройки → Основные → VPN и управление устройством."
p["PayloadDisplayName"] = display
p["PayloadIdentifier"] = "personal.english.webclips." + key
p["PayloadUUID"] = str(uuid.uuid4()).upper()
assert set(p) == set(ref) and set(clip) == set(ref["PayloadContent"][0])
assert clip["FullScreen"] is True and clip["IgnoreManifestScope"] is True
out = pathlib.Path(key + "-tile.mobileconfig"); out.write_bytes(plistlib.dumps(p))
chk = plistlib.loads(out.read_bytes()); print("ok", out, out.stat().st_size, chk["PayloadContent"][0]["Label"], chk["PayloadContent"][0]["URL"])
