# flippy-web

Frontend PWA de Flippy: Next.js 14 (App Router) + TypeScript. UI de chat, service worker, manifest.

## Desarrollo local

```bash
npm install
cp .env.example .env.local   # completar NEXT_PUBLIC_API_BASE_URL
npm run dev
```

Abrí [http://localhost:3000](http://localhost:3000) — redirige a `/chat`.

## Tests

```bash
npm test
```

## Build de producción

```bash
npm run build
```

### Nota — build falla por SSL en este entorno (Avast)

Si `npm run build` falla con `unable to verify the first certificate` al descargar las
fuentes de Google (Cormorant Garamond / Lato), es porque Avast Antivirus intercepta TLS
localmente con su propio certificado raíz, que Node no confía por defecto. Exportalo una
vez desde el almacén de Windows y pasalo por `NODE_EXTRA_CA_CERTS`:

```powershell
$cert = Get-ChildItem -Path Cert:\LocalMachine\Root | Where-Object { $_.Subject -like "*Avast*" }
$b64 = [Convert]::ToBase64String($cert[0].RawData, 'InsertLineBreaks')
"-----BEGIN CERTIFICATE-----`n$b64`n-----END CERTIFICATE-----" | Out-File avast-root.pem -Encoding ascii
```

```bash
export NODE_EXTRA_CA_CERTS="/ruta/a/avast-root.pem"
npm run build
```

Esto es específico de esta máquina de desarrollo — no aplica en Railway/CI (sin Avast interceptando TLS ahí).

## Arquitectura

- `services/api.ts`: único punto de llamadas al backend (`flippy-api`). Sin axios — fetch nativo.
- `app/globals.css`: design tokens de marca (ver SPEC.md §C Brand Token Sheet) como CSS custom properties.
- `public/manifest.json` + `public/sw.js`: PWA — instalación fullscreen, shell cacheado offline.
- Sin modo oscuro en esta fase (SPEC.md §11).

## Deploy

Railway, deploy continuo desde `main`. Sin Vercel — ver SPEC.md §5.
