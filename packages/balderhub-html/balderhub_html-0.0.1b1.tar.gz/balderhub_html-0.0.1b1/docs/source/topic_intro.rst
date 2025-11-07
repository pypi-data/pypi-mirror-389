Introduction into HTML
**********************

HTML, or HyperText Markup Language, is the standard markup language used to create and structure content on the web. It
serves as the backbone of web pages, defining the meaning and layout of text, images, multimedia, and other elements.

What is HTML?
=============

**HTML (HyperText Markup Language)** is the standard markup language used to structure content on the web. It consists
of **elements** (also called *tags*), which describe the semantic meaning of content—such as headings, paragraphs,
links, images, forms, and more. HTML documents are essentially text files with a ``.html`` extension that can be viewed
in any web browser.

HTML enables the creation of structured documents by denoting elements such as headings, paragraphs, lists, links, and
forms. When combined with CSS (Cascading Style Sheets) for styling and JavaScript for interactivity, it forms the core
technologies of the World Wide Web.

Basic Structure of an HTML Document
-----------------------------------

Every HTML document follows a basic skeleton:

.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Document Title</title>
    </head>
    <body>
        <!-- Content goes here -->
        <h1>Main Heading</h1>
        <p>This is a paragraph of text.</p>
    </body>
    </html>

* ``<!DOCTYPE html>``: Declares the document type and version (HTML5 in this case).
* ``<html>``: The root element that wraps all content.
* ``<head>``: Contains meta-information like the title, character encoding, and links to stylesheets or scripts.
* ``<body>``: Holds the visible content of the page, such as text, images, and other media.

Key HTML Elements
-----------------

HTML uses tags (e.g., ``<tag>content</tag>``) to define elements. Here are some fundamental ones relevant to web
testing:

* **Headings**: ``<h1>`` to ``<h6>`` for titles and subtitles.
* **Paragraphs**: ``<p>`` for blocks of text.
* **Links**: ``<a href="url">Link Text</a>`` for hyperlinks.
* **Images**: ``<img src="image.jpg" alt="Description">`` for embedding images.
* **Lists**: ``<ul>`` for unordered lists, ``<ol>`` for ordered lists, with ``<li>`` for list items.
* **Forms**: ``<form>`` with inputs like ``<input type="text">``, ``<button>``, etc., for user interaction.
* **Tables**: ``<table>``, ``<tr>``, ``<th>``, ``<td>`` for tabular data.
* **Div and Span**: ``<div>`` for block-level grouping and ``<span>`` for inline grouping, often used for styling or scripting.

Attributes can be added to tags for additional information, such as ``id``, ``class``, ``style``, or event handlers
like ``onclick``.

Why HTML Matters in Testing with BalderHub-HTML
===============================================

The balderhub-html package provides pre-built scenarios and features for interacting with and validating HTML
structures in your tests.  By understanding HTML basics, you can effectively
use the features provided by this package to ensure your web applications render correctly, maintain accessibility, and
function as expected across different browsers.

If you're testing web content, consider common pitfalls like malformed tags, missing attributes, or semantic errors,
which this package can help detect through automated scenarios.

For more advanced topics, refer to the official HTML specification or resources like MDN Web Docs. In the next
sections, we'll dive into how to use balderhub-html features to incorporate HTML testing into your Balder workflows.