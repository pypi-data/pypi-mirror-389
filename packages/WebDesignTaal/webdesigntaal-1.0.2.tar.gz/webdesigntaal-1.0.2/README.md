# WebDesignTaal
![](https://img.shields.io/github/stars/TJouleL/WebDesignTaal) ![](https://img.shields.io/github/forks/TJouleL/WebDesignTaal) ![](https://img.shields.io/github/tag/TJouleL/WebDesignTaal) ![](https://img.shields.io/github/release/TJouleL/WebDesignTaal) ![](https://img.shields.io/github/issues/TJouleL/WebDesignTaal)

WebDesignTaal is een programmeertaal die is ontworpen om het schrijven van webpagina's te vereenvoudigen met een intuïtieve Nederlandse syntaxis. Het compileert je code naar gestructureerde HTML.

## Installatie

```bash
pip install WebDesignTaal
```

## Gebruik

### Command-line Tool

Je kunt een `.wdt` bestand converteren naar een HTML-website met het `wdt` commando:

```bash
wdt <pad_naar_bestand.wdt>
```

Dit genereert een `output` map (in dezelfde directory als het `.wdt` bestand) met daarin een `index.html` bestand.

### Als Python Module

Je kunt de `render_code` functie ook direct in je Python-code gebruiken:

```python
from WebDesignTaal.wdt_parser import render_code

wdt_code = """
document;
  head;
    metadata charset="utf-8";
    metadata name="viewport" content="width=device-width, initial-scale=1.0";
    metadata title="Mijn Webpagina";
  body;
    kop1; Welkom bij WebDesignTaal!
    tekst; Dit is een voorbeeld van een paragraaf.
"""

html_output = render_code(wdt_code)
print(html_output)
```

## WebDesignTaal Syntax Uitleg

WebDesignTaal gebruikt een eenvoudige, op indentatie gebaseerde syntax om de structuur van webpagina's te definiëren.

*   **Indentatie:** De hiërarchie van elementen wordt bepaald door indentatie. Gebruik **vier spaties** per niveau.
*   **Tag Naam:** Elk element begint met de Nederlandse tag naam (bijv. `document`, `kop1`, `tekst`).
*   **Content:** De tekstuele inhoud van een element volgt na een puntkomma (`;`). Als er geen content is, kan de puntkomma weggelaten worden, maar het is goede praktijk om deze te behouden voor consistentie.
*   **Attributen:** Attributen worden na de tag naam geplaatst en voor de puntkomma, gescheiden door spaties. Attributen bestaan uit een sleutel-waarde paar (`sleutel=waarde`). Waarden die spaties bevatten, moeten tussen aanhalingstekens (`"` of `'`) staan. Voor waarden zonder spaties zijn aanhalingstekens optioneel.
*   **Commentaar:** Je kunt commentaar toevoegen aan je code door een `#` te gebruiken. Alles na de `#` op dezelfde regel wordt genegeerd door de parser. Let wel op dat je dit op een nieuwe regel moet doen. Als je hem gebruikt na de content van een tag maakt het deel van de content zelf.
*   **Regelafbrekingen:** Extra lege regels (enters) tussen elementen worden genegeerd en kunnen gebruikt worden om je code overzichtelijker te maken.

**Voorbeeld:**

```wdt
document;
  head;
    metadata charset="utf-8";
    metadata name="viewport" content="width=device-width, initial-scale=1.0";
    metadata title="Mijn Webpagina";
  body;
    kop1 id=hoofdtitel kleur=rood; Welkom bij WebDesignTaal! 
    # Dit is commentaar

    tekst klasse="intro"; Dit is een voorbeeld van een paragraaf.
    link adres="https://www.example.com"; Ga naar Example.com
```

## Onderliggende Structuur: Child-Parent Systeem met Nodes

WebDesignTaal vertaalt je code naar een interne boomstructuur van 'nodes' (knopen), vergelijkbaar met hoe browsers een Document Object Model (DOM) van HTML-pagina's maken. Elk element in je WDT-code wordt een node, en de indentatie bepaalt de relatie tussen deze nodes:

*   Een minder ingesprongen node is de **parent** (ouder) van de meer ingesprongen nodes die er direct onder staan.
*   De meer ingesprongen nodes zijn de **children** (kinderen) van de parent node.

Deze hiërarchische structuur zorgt ervoor dat de gecompileerde HTML correct genest is, wat essentieel is voor de structuur en weergave van webpagina's. Bijvoorbeeld, een `head` node is een kind van de `document` node, en een `tekst` node kan een kind zijn van een `body` node.

**Voorbeeld van hiërarchie:**

```wdt
document;  # Parent
  head;    # Kind van 'document'
    metadata; # Kind van 'head'
  body;    # Kind van 'document'
    kop1;    # Kind van 'body'
    tekst;   # Kind van 'body'
```

## Attributen en Stijlvertalingen

WebDesignTaal biedt een flexibele manier om attributen en stijlen toe te passen op je elementen. Je kunt de meeste standaard HTML-attributen direct gebruiken, evenals Nederlandse vertalingen voor veelvoorkomende attributen en CSS-stijlen.

### Standaard Attributen

WebDesignTaal herkent en verwerkt de meeste standaard HTML-attributen direct. Je kunt deze gebruiken zoals je gewend bent in HTML:
`id`, `class`, `href`, `src`, `alt`, `title`, `name`, `value`, `type`, `placeholder`, `checked`, `disabled`, `readonly`, `action`, `method`, `for`, `rel`, `target`, `width`, `height`, `cols`, `rows`, `maxlength`, `min`, `max`, `step`, `selected`, `autocomplete`, `download`, `role`, `lang`, `tabindex`, `aria-label`, `style`

### Nederlandse Attribuut Aliassen

Voor een meer Nederlandse ervaring kun je de volgende aliassen gebruiken voor veelvoorkomende attributen:

| WDT Attribuut | HTML Equivalent |
| :------------ | :-------------- |
| `bron`        | `src`           |
| `breedte`     | `width`         |
| `hoogte`      | `length`        |
| `rijen`       | `rows`          |
| `kolommen`    | `cols`          |
| `taal`        | `lang`          |
| `adres`       | `href`          |
| `alttekst`    | `alt`           |
| `karakterset` | `charset`       |
| `citeer`      | `cite`          |
| `verborgen`   | `hidden`        |

### Stijl Attributen

Je kunt CSS-stijlen direct als attributen opgeven in WebDesignTaal. De taal vertaalt veel Nederlandse stijl-eigenschappen naar hun CSS-equivalenten, die vervolgens worden toegepast via het `style`-attribuut in de HTML.

**Voorbeeld:** `tekst kleur=rood lettergrootte=16px; Dit is rode tekst.`

Hier zijn enkele van de ondersteunde stijl-eigenschappen:

| WDT Stijl Eigenschap | CSS Eigenschap     |
| :------------------- | :----------------- |
| `kleur`              | `color`            |
| `achtergrondkleur`   | `background-color` |
| `achtergrond`        | `background`       |
| `lettertype`         | `font-family`      |
| `lettergrootte`      | `font-size`        |
| `letterstijl`        | `font-style`       |
| `lettergewicht`      | `font-weight`      |
| `tekstuitlijning`    | `text-align`       |
| `tekstdecoratie`     | `text-decoration`  |
| `teksttransformatie` | `text-transform`   |
| `regelhoogte`        | `line-height`      |
| `woordafstand`       | `word-spacing`     |
| `letterafstand`      | `letter-spacing`   |
| `breedte`            | `width`            |
| `hoogte`             | `height`           |
| `marge`              | `margin`           |
| `margeboven`         | `margin-top`       |
| `margeonder`         | `margin-bottom`    |
| `margelinks`         | `margin-left`      |
| `margerechts`        | `margin-right`     |
| `opvulling`          | `padding`          |
| `opvullingboven`     | `padding-top`      |
| `opvullingonder`     | `padding-bottom`   |
| `opvullinglinks`     | `padding-left`     |
| `opvullingrechts`    | `padding-right`    |
| `rand`               | `border`           |
| `randkleur`          | `border-color`     |
| `randstijl`          | `border-style`     |
| `randdikte`          | `border-width`     |
| `afronding`          | `border-radius`    |
| `positie`            | `position`         |
| `boven`              | `top`              |
| `onder`              | `bottom`           |
| `links`              | `left`             |
| `rechts`             | `right`            |
| `zweven`             | `float`            |
| `weergave`           | `display`          |
| `zichtbaarheid`      | `visibility`       |
| `zindex`             | `z-index`          |
| `schaduw`            | `box-shadow`       |
| `tektschaduw`        | `text-shadow`      |
| `doorzichtigheid`    | `opacity`          |
| `cursor`             | `cursor`           |
| `achtergrondafbeelding`| `background-image`|
| `achtergrondpositie` | `background-position`|
| `achtergrondherhaling`| `background-repeat`|
| `achtergronddekking` | `background-size`  |
| `animatie`           | `animation`        |
| `animatienaam`       | `animation-name`   |
| `animatieduur`       | `animation-duration`|
| `overgang`           | `transition`       |

### Stijl Waarde Aliassen

Ook voor veelgebruikte CSS-waarden zijn Nederlandse aliassen beschikbaar:

| WDT Waarde | CSS Equivalent |
| :--------- | :------------- |
| `rood`     | `red`          |
| `blauw`    | `blue`         |
| `groen`    | `green`        |
| `geel`     | `yellow`       |
| `zwart`    | `black`        |
| `wit`      | `white`        |
| `grijs`    | `gray`         |
| `lichtgrijs`| `lightgray`   |
| `donkergrijs`| `darkgray`   |
| `lichtblauw`| `lightblue`   |
| `donkerblauw`| `darkblue`   |
| `lichtgroen`| `lightgreen`  |
| `donkergroen`| `darkgreen`  |
| `lichtrood` | `lightred`    |
| `donkerrood`| `darkred`    |
| `lichtgeel` | `lightyellow` |
| `donkergeel`| `darkyellow`  |
| `paars`    | `purple`       |
| `oranje`   | `orange`       |
| `roze`     | `pink`         |
| `bruin`    | `brown`        |
| `transparant`| `transparent` |
| `links`    | `left`         |
| `rechts`   | `right`        |
| `midden`   | `center`       |
| `gecentreerd`| `center`     |
| `boven`    | `top`          |
| `onder`    | `bottom`       |
| `blok`     | `block`        |
| `inline`   | `inline`       |
| `flex`     | `flex`         |
| `geen`     | `none`         |
| `vet`      | `bold`         |
| `normaal`  | `normal`       |
| `cursief`  | `italic`       |
| `absoluut` | `absolute`     |
| `relatief` | `relative`     |
| `vast`     | `fixed`        |
| `verborgen`| `hidden`       |
| `zichtbaar`| `visible`      |
| `stippel`  | `dotted`       |
| `gestreept`| `dashed`       |
| `doorgetrokken`| `solid`     |

## Beschikbare Tags (Elementen)

Hieronder vind je een overzicht van alle beschikbare tags in WebDesignTaal, inclusief hun functie, vereisten en voorbeeldcode.

### `document`
*   **Doel:** De root van elk WebDesignTaal document, definieert de basisstructuur van je webpagina.
*   **Vereisten:** Geen specifieke attributen. Bevat meestal `head` en `body` als kinderen.
*   **WDT Voorbeeld:**
    ```wdt
    document;
      head;
      body;
    ```
*   **HTML Output:**
    ```html
    <html>
      <head>
      </head>
      <body>
      </body>
    </html>
    ```

### `head`
*   **Doel:** Bevat metadata voor het document, zoals de titel, karakterset en links naar stylesheets.
*   **Vereisten:** Geen specifieke attributen. Bevat vaak `metadata` tags.
*   **WDT Voorbeeld:**
    ```wdt
    document;
      head;
        metadata charset="utf-8";
        metadata title="Mijn Titel";
    ```
*   **HTML Output:**
    ```html
    <html>
      <head>
        <meta charset="utf-8">
        <meta title="Mijn Titel">
      </head>
      <body>
      </body>
    </html>
    ```

### `body`
*   **Doel:** Bevat de zichtbare inhoud van je webpagina, zoals tekst, afbeeldingen en links.
*   **Vereisten:** Geen specifieke attributen. Bevat alle zichtbare elementen zoals koppen, paragrafen, etc.
*   **WDT Voorbeeld:**
    ```wdt
    document;
      body;
        kop1; Welkom!
        tekst; Dit is de inhoud.
    ```
*   **HTML Output:**
    ```html
    <body>
      <h1>Welkom!</h1>
      <h2>Dit is de inhoud.</h2>
    </body>
    ```

### `kop1` tot `kop6`
*   **Doel:** Definieert koppen van verschillende niveaus, van de belangrijkste (`kop1`) tot de minst belangrijke (`kop6`).
*   **Vereisten:** Tekstuele inhoud.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      kop1; Hoofdtitel
      kop2; Subtitel
      kop6; Kleinste kop
    ```
*   **HTML Output:**
    ```html
    <body>
      <h1>Hoofdtitel</h1>
      <h2>Subtitel</h2>
      <h6>Kleinste kop</h6>
    </body>
    ```

### `tekst`
*   **Doel:** Creëert een paragraaf tekst.
*   **Vereisten:** Tekstuele inhoud.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      tekst; Dit is een normale paragraaf.
      tekst kleur=blauw; Deze tekst is blauw.
    ```
*   **HTML Output:**
    ```html
    <body>
      <p>Dit is een normale paragraaf.</p>
      <p style="color:blue">Deze tekst is blauw.</p>
    </body>
    ```

### `opsomming_lijst`
*   **Doel:** Creëert een ongeordende lijst (met opsommingstekens). Bevat `lijst_item` als kinderen.
*   **Vereisten:** Geen specifieke attributen.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      opsomming_lijst;
        lijst_item; Eerste item
        lijst_item; Tweede item
    ```
*   **HTML Output:**
    ```html
    <body>
      <ul>
        <li>Eerste item</li>
        <li>Tweede item</li>
      </ul>
    </body>
    ```

### `getal_lijst`
*   **Doel:** Creëert een geordende lijst (met nummers). Bevat `lijst_item` als kinderen.
*   **Vereisten:** Geen specifieke attributen.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      getal_lijst;
        lijst_item; Eerste genummerde item
        lijst_item; Tweede genummerde item
    ```
*   **HTML Output:**
    ```html
    <body>
      <ol>
        <li>Eerste genummerde item</li>
        <li>Tweede genummerde item</li>
      </ol>
    </body>
    ```

### `lijst_item`
*   **Doel:** Een individueel item binnen een lijst. Moet een kind zijn van `opsomming_lijst` of `getal_lijst`.
*   **Vereisten:** Tekstuele inhoud. Moet binnen een lijst-tag staan.
*   **WDT Voorbeeld:** (Zie `opsomming_lijst` en `getal_lijst` voor context)
    ```wdt
    opsomming_lijst;
      lijst_item; Een item
    ```
*   **HTML Output:**
    ```html
    <ul>
      <li>Een item</li>
    </ul>
    ```

### `afbeelding`
*   **Doel:** Voegt een afbeelding toe aan de webpagina.
*   **Vereisten:** Het attribuut `bron` (pad naar de afbeelding) en bij voorkeur `alttekst` (alternatieve tekst voor toegankelijkheid).
*   **WDT Voorbeeld:**
    ```wdt
    body;
      afbeelding bron="pad/naar/afbeelding.jpg" alttekst="Beschrijving van afbeelding";
    ```
*   **HTML Output:**
    ```html
    <body>
      <img src="pad/naar/afbeelding.jpg" alt="Beschrijving van afbeelding">
    </body>
    ```

### `link`
*   **Doel:** Creëert een hyperlink naar een andere pagina of bron.
*   **Vereisten:** Het attribuut `adres` (de URL waar de link naartoe verwijst).
*   **WDT Voorbeeld:**
    ```wdt
    body;
      link adres="https://www.google.com"; Ga naar Google
    ```
*   **HTML Output:**
    ```html
    <body>
      <a href="https://www.google.com">Ga naar Google</a>
    </body>
    ```

### `gedeelte`
*   **Doel:** Een generieke container voor content, handig voor het groeperen van elementen voor styling of scripting.
*   **Vereisten:** Geen specifieke attributen.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      gedeelte id=mijnSectie klasse=container;
        kop2; Dit is een sectie
        tekst; Content binnen de sectie.
    ```
*   **HTML Output:**
    ```html
    <body>
      <div id="mijnSectie" class="container">
        <h2>Dit is een sectie</h2>
        <p>Content binnen de sectie.</p>
      </div>
    </body>
    ```

### `artikel`
*   **Doel:** Representeert onafhankelijke, zelfstandige content, zoals een blogpost of nieuwsartikel.
*   **Vereisten:** Geen specifieke attributen.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      artikel;
        kop2; Nieuwsbericht
        tekst; Dit is de inhoud van het nieuwsbericht.
    ```
*   **HTML Output:**
    ```html
    <body>
      <article>
        <h2>Nieuwsbericht</h2>
        <p>Dit is de inhoud van het nieuwsbericht.</p>
      </article>
    </body>
    ```

### `audio`
*   **Doel:** Voegt audio content toe aan de webpagina.
*   **Vereisten:** Het attribuut `bron` (pad naar het audiobestand).
*   **WDT Voorbeeld:**
    ```wdt
    body;
      audio bron="pad/naar/audio.mp3";
    ```
*   **HTML Output:**
    ```html
    <body>
      <audio src="pad/naar/audio.mp3"></audio>
    </body>
    ```

### `video`
*   **Doel:** Voegt video content toe aan de webpagina.
*   **Vereisten:** Het attribuut `bron` (pad naar het videobestand).
*   **WDT Voorbeeld:**
    ```wdt
    body;
      video bron="pad/naar/video.mp4" breedte=640 hoogte=480;
    ```
*   **HTML Output:**
    ```html
    <body>
      <video src="pad/naar/video.mp4" width="640" height="480"></video>
    </body>
    ```

### `quote`
*   **Doel:** Gebruikt voor lange citaten die uit een andere bron komen.
*   **Vereisten:** Tekstuele inhoud.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      quote; Dit is een lang citaat van een andere bron.
    ```
*   **HTML Output:**
    ```html
    <body>
      <blockquote>Dit is een lang citaat van een andere bron.</blockquote>
    </body>
    ```

### `lijn`
*   **Doel:** Tekent een horizontale scheidingslijn op de webpagina.
*   **Vereisten:** Geen inhoud of attributen nodig.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      tekst; Boven de lijn.
      lijn;
      tekst; Onder de lijn.
    ```
*   **HTML Output:**
    ```html
    <body>
      <p>Boven de lijn.</p>
      <hr>
      <p>Onder de lijn.</p>
    </body>
    ```

### `schuingedrukt`
*   **Doel:** Maakt de ingesloten tekst schuingedrukt.
*   **Vereisten:** Tekstuele inhoud.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      schuingedrukt; Dit is schuingedrukte tekst.
    ```
*   **HTML Output:**
    ```html
    <body>
      <i>Dit is schuingedrukte tekst.</i>
    </body>
    ```

### `dikgedrukt`
*   **Doel:** Maakt de ingesloten tekst dikgedrukt.
*   **Vereisten:** Tekstuele inhoud.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      dikgedrukt; Dit is dikgedrukte tekst.
    ```
*   **HTML Output:**
    ```html
    <body>
      <b>Dit is dikgedrukte tekst.</b>
    </body>
    ```

### `onderlijndrukt`
*   **Doel:** Onderstreept de ingesloten tekst.
*   **Vereisten:** Tekstuele inhoud.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      onderlijndrukt; Dit is onderlijnde tekst.
    ```
*   **HTML Output:**
    ```html
    <body>
      <u>Dit is onderlijnde tekst.</u>
    </body>
    ```

### `metadata`
*   **Doel:** Definieert metadata over het HTML-document, zoals de karakterset, viewport instellingen of de paginatitel.
*   **Vereisten:** Attributen zoals `charset`, `name`, `content`, `title`.
*   **WDT Voorbeeld:**
    ```wdt
    head;
      metadata charset="utf-8";
      metadata name="description" content="Een beschrijving van de pagina";
    ```
*   **HTML Output:**
    ```html
    <head>
      <meta charset="utf-8">
      <meta name="description" content="Een beschrijving van de pagina">
    </head>
    ```

### `tabel`
*   **Doel:** Creëert een HTML-tabel voor het weergeven van gestructureerde gegevens. Bevat `tabelrij` als kinderen.
*   **Vereisten:** Geen specifieke attributen.
*   **WDT Voorbeeld:**
    ```wdt
    body;
      tabel;
        tabelrij;
          tabelcel; Rij 1, Cel 1
          tabelcel; Rij 1, Cel 2
        tabelrij;
          tabelcel; Rij 2, Cel 1
          tabelcel; Rij 2, Cel 2
    ```
*   **HTML Output:**
    ```html
    <body>
      <table>
        <tr>
          <td>Rij 1, Cel 1</td>
          <td>Rij 1, Cel 2</td>
        </tr>
        <tr>
          <td>Rij 2, Cel 1</td>
          <td>Rij 2, Cel 2</td>
        </tr>
      </table>
    </body>
    ```

### `tabelrij`
*   **Doel:** Definieert een rij in een HTML-tabel. Moet een kind zijn van `tabel`. Bevat `tabelcel` als kinderen.
*   **Vereisten:** Moet binnen een `tabel`-tag staan.
*   **WDT Voorbeeld:** (Zie `tabel` voor context)
    ```wdt
    tabel;
      tabelrij;
        tabelcel; Cel in rij
    ```
*   **HTML Output:**
    ```html
    <table>
      <tr>
        <td>Cel in rij</td>
      </tr>
    </table>
    ```

### `tabelcel`
*   **Doel:** Definieert een cel in een HTML-tabel. Moet een kind zijn van `tabelrij`.
*   **Vereisten:** Tekstuele inhoud. Moet binnen een `tabelrij`-tag staan.
*   **WDT Voorbeeld:** (Zie `tabel` voor context)
    ```wdt
    tabelrij;
      tabelcel; Inhoud van de cel
    ```
*   **HTML Output:**
    ```html
    <tr>
      <td>Inhoud van de cel</td>
    </tr>
    ```

### `stijl`

* **Doel:** Linkt een extern CSS-stylesheet naar de website.
* **Vereisten:** Vereist een `adres`-attribuut dat verwijst naar het CSS-bestand.
* **WDT Voorbeeld:**

  ```wdt
  stijl adres="stijl.css";
  ```
* **HTML Output:**

  ```html
  <link rel="stylesheet" type="text/css" href="stijl.css">
  ```

### `code`

* **Doel:** Voegt een extern of inline JavaScript-script toe aan de website.
* **Vereisten:** Vereist een `bron`-attribuut voor externe scripts, of inline code na een `;`.
* **WDT Voorbeeld:**

  ```wdt
  code bron="script.js";
  ```

* **HTML Output:**
  **Extern script:**

  ```html
  <script src="script.js"></script>
  ```


  
