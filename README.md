# Publicador Factory AI Web

Publica en Instagram (reels, historias, posts y carruseles) a la hora del calendario, gratis y sin tope de 20 al mes.
Funciona con la API oficial de Instagram y GitHub Actions. No necesita servidor.

## Cómo funciona
- `calendario.csv`: una fila por publicación. Solo se publican las filas con estado `programado` cuya hora ya llegó (hora de Chile).
- `media/`: archivos que se publican. Las imágenes van en **JPG**; los videos en **MP4**. GitHub Pages los deja en una URL pública, que es lo que pide Instagram.
- `textos/`: textos largos de cada publicación (la columna `texto` puede tener el texto o el nombre de un `.txt`).
- Cada 15 minutos, GitHub corre `publicar.py`, publica lo que toca y anota en el calendario `publicado` (con el ID de Instagram) o `error` (con el motivo).

### Columnas de `calendario.csv`
| Columna | Ejemplo | Nota |
|---|---|---|
| id | `h-11-20-09` | único |
| fecha_hora | `2026-11-20 09:00` | hora de Chile |
| tipo | `REEL`, `HISTORIA`, `POST`, `CARRUSEL` | |
| archivos | `historia-s09.jpg` · carrusel: `a.jpg\|b.jpg\|c.jpg` | 2 a 10 en carrusel |
| portada | `portada-r7.jpg` | solo reels (opcional) |
| texto | texto o `c4-orfelia.txt` | las historias no llevan texto |
| estado | `borrador` → `programado` → `publicado` / `error` / `atrasado` | solo `programado` se publica |

## Puesta en marcha (una vez)
1. **Repositorio:** crear en GitHub el repositorio **público** `factoryai-publicador` (público para que GitHub Pages sirva los archivos gratis; los secretos quedan ocultos igual). Subir estos archivos.
2. **GitHub Pages:** Settings → Pages → «Deploy from a branch» → `main` / `(root)`. Anotar la URL (ej. `https://factoryaiweb-star.github.io/factoryai-publicador/`).
3. **Variable:** Settings → Secrets and variables → Actions → pestaña *Variables* → `PUBLIC_BASE_URL` = esa URL.
4. **App de Meta** (hecha el 18-11-2026: «Factory AI Publicador», caso de uso Instagram, portfolio Factory AI web). Las apps nuevas usan **inicio de sesión unificado**, así que el token es un **token de usuario del sistema** (no caduca):
   - business.facebook.com → Configuración del negocio → Usuarios → **Usuarios del sistema** → Agregar (nombre `publicador`, rol Administrador).
   - En ese usuario: **Asignar activos** → la cuenta de Instagram `@factoryaiweb` (control total) y la app «Factory AI Publicador».
   - **Generar token** → app «Factory AI Publicador» → caducidad «Nunca» → permisos `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`.
   - La cuenta de Instagram debe ser de tipo **Empresa** y estar vinculada a la página de Facebook del negocio.
5. **Secretos** (Settings → Secrets and variables → Actions → *Secrets*), pegados directo ahí, **nunca en un chat**:
   - `IG_TOKEN`: el token del usuario del sistema.
   - `IG_USER_ID`: el ID de la cuenta de Instagram para empresas (lo da Configuración del negocio → Cuentas → Cuentas de Instagram, o el Explorador de la API Graph con `me/accounts?fields=instagram_business_account`).
   - (`GH_PAT` ya no hace falta: este token no caduca.)
6. **Prueba:** en `calendario.csv`, cambiar `prueba-1` a `programado` con una hora ya pasada → Actions → «Publicar en Instagram» → *Run workflow*. Debe aparecer una historia y la fila queda `publicado`.

## Límites
- Instagram: hasta 50 publicaciones por API cada 24 h (un carrusel cuenta como una).
- No se pueden poner stickers (encuesta, enlace) en historias por API.
- GitHub puede atrasar unos minutos la ejecución programada.
