var BACKEND_URL = 'https://YOUR_CLOUD_RUN_URL';

function onOpen(e) {
  DocumentApp.getUi()
    .createMenu('Docs to Anki')
    .addItem('Convert to Anki Cards', 'showSidebar')
    .addToUi();
}

function showSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('Docs to Anki')
    .setWidth(300);
  DocumentApp.getUi().showSidebar(html);
}

function extractDocContent() {
  var doc = DocumentApp.getActiveDocument();
  var body = doc.getBody();
  var numChildren = body.getNumChildren();
  var paragraphs = [];

  for (var i = 0; i < numChildren; i++) {
    var child = body.getChild(i);
    var type = child.getType();

    if (type === DocumentApp.ElementType.TABLE) {
      paragraphs.push(extractTable(child.asTable()));
    } else if (type === DocumentApp.ElementType.PARAGRAPH) {
      var result = extractParagraph(child.asParagraph());
      if (result) paragraphs.push(result);
    }
  }

  return {
    paragraphs: paragraphs,
    docTitle: doc.getName()
  };
}

function extractParagraph(para) {
  var text = para.getText().trim();
  var images = extractImagesFromParagraph(para);

  if (!text && images.length === 0) return null;

  var heading = para.getHeading();
  var isHeading = heading !== DocumentApp.ParagraphHeading.NORMAL;
  var isBold = text ? isEntirelyBold(para) : false;
  var textColor = text ? getTextColor(para) : null;

  return {
    text: text,
    is_bold: isBold,
    is_heading: isHeading,
    text_color: textColor,
    is_table: false,
    table_html: null,
    images: images
  };
}

function extractTable(table) {
  var numRows = table.getNumRows();
  var html = '<table>';

  for (var r = 0; r < numRows; r++) {
    var row = table.getRow(r);
    var numCells = row.getNumCells();
    var tag = (r === 0) ? 'th' : 'td';
    html += '<tr>';
    for (var c = 0; c < numCells; c++) {
      var cellText = row.getCell(c).getText().trim();
      html += '<' + tag + '>' + escapeHtml(cellText) + '</' + tag + '>';
    }
    html += '</tr>';
  }

  html += '</table>';

  var textContent = [];
  for (var r = 0; r < numRows; r++) {
    var row = table.getRow(r);
    var rowText = [];
    for (var c = 0; c < row.getNumCells(); c++) {
      rowText.push(row.getCell(c).getText().trim());
    }
    textContent.push(rowText.join(' | '));
  }

  return {
    text: textContent.join('\n'),
    is_bold: false,
    is_heading: false,
    text_color: null,
    is_table: true,
    table_html: html,
    images: []
  };
}

function extractImagesFromParagraph(para) {
  var images = [];
  var numChildren = para.getNumChildren();

  for (var i = 0; i < numChildren; i++) {
    var child = para.getChild(i);
    if (child.getType() === DocumentApp.ElementType.INLINE_IMAGE) {
      var blob = child.asInlineImage().getBlob();
      var b64 = Utilities.base64Encode(blob.getBytes());
      images.push(b64);
    }
  }

  return images;
}

function isEntirelyBold(paragraph) {
  var text = paragraph.editAsText();
  var content = paragraph.getText();
  if (!content || content.trim().length === 0) return false;

  for (var i = 0; i < content.length; i++) {
    if (content[i] === ' ' || content[i] === '\t') continue;
    if (!text.isBold(i)) return false;
  }
  return true;
}

function getTextColor(paragraph) {
  var text = paragraph.editAsText();
  var content = paragraph.getText();
  if (!content || content.trim().length === 0) return null;

  for (var i = 0; i < content.length; i++) {
    if (content[i] === ' ' || content[i] === '\t') continue;
    var color = text.getForegroundColor(i);
    if (color) return color;
    break;
  }
  return null;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function sendToBackend(paragraphs) {
  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ paragraphs: paragraphs }),
    muteHttpExceptions: true
  };

  var response = UrlFetchApp.fetch(BACKEND_URL + '/api/extract', options);

  if (response.getResponseCode() !== 200) {
    throw new Error('Backend error: ' + response.getContentText());
  }

  return JSON.parse(response.getContentText());
}

function generateDeck(cards, deckName) {
  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ cards: cards, deck_name: deckName }),
    muteHttpExceptions: true
  };

  var response = UrlFetchApp.fetch(BACKEND_URL + '/api/generate', options);

  if (response.getResponseCode() !== 200) {
    throw new Error('Backend error: ' + response.getContentText());
  }

  return Utilities.base64Encode(response.getContent());
}

function showCardReview(cardsJson, deckName) {
  var template = HtmlService.createTemplateFromFile('CardReview');
  template.cardsJson = cardsJson;
  template.deckName = deckName;
  var html = template.evaluate()
    .setWidth(700)
    .setHeight(500);
  DocumentApp.getUi().showModalDialog(html, 'Review Anki Cards');
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}
