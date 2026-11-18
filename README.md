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
4. **App de Meta** (developers.facebook.com, con la cuenta de Factory AI Web):
   - Crear app → caso de uso de **Instagram** («Administrar mensajes y contenido en Instagram»).
   - En «Configuración de la API con inicio de sesión de Instagram», agregar la cuenta `@factoryaiweb` y **Generar token** con los permisos `instagram_business_basic` y `instagram_business_content_publish`.
   - La app puede quedar en modo desarrollo: es para tu propia cuenta.
   - La cuenta de Instagram debe ser de tipo **Empresa** (las cuentas de Creador no pueden publicar historias por API).
5. **Secretos** (Settings → Secrets and variables → Actions → *Secrets*), pegados directo ahí, **nunca en un chat**:
   - `IG_TOKEN`: el token generado.
   - `IG_USER_ID`: el ID de la cuenta de Instagram que muestra la misma pantalla.
   - `GH_PAT`: token de GitHub *fine-grained* solo para este repo, con permiso «Secrets: Read and write» (sirve para renovar el token de Instagram solo, los días 1 y 15).
6. **Prueba:** en `calendario.csv`, cambiar `prueba-1` a `programado` con una hora ya pasada → Actions → «Publicar en Instagram» → *Run workflow*. Debe aparecer una historia y la fila queda `publicado`.

## Límites
- Instagram: hasta 50 publicaciones por API cada 24 h (un carrusel cuenta como una).
- No se pueden poner stickers (encuesta, enlace) en historias por API.
- GitHub puede atrasar unos minutos la ejecución programada.
