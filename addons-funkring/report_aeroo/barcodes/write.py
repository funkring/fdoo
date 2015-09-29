# -*- coding: utf-8 -*-
"""
Barcodes for Python - Module for writing.
Copyright 2009  Peter Gebauer

Cairo backend for writing barcodes.

"Barcodes for Python" is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

"Barcodes for Python" is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
(see file COPYING) along with "Barcodes for Python".
If not, see <http://www.gnu.org/licenses/>.
"""
import warnings
import StringIO
import cairo

CAIRO_RESOLUTION_PER_INCH = 72.0
CAIRO_RESOLUTION_PER_M = 72.0 / 0.0254
CAIRO_RESOLUTION_PER_MM = 72.0 / 25.4

COLOR_BLACK = (0.0, 0.0, 0.0, 1.0)
COLOR_WHITE = (1.0, 1.0, 1.0, 1.0)

class Render(object):
    """
    A render object hold some information on colors and geometries needed
    when rendering a barcode.
    A render implementation needs the ability to write to SVG, PNG and PostScript.
    All colors used must be four float tuples.
    """

    def __init__(self, barcode, **kwargs):
        """
        Valid keywords:
        color_on        Defaults to COLOR_BLACK.
        color_off       Defaults to None. (i.e not drawn)
        color_bg        Defaults to COLOR_WHITE.
        color_margin    Defaults to COLOR_WHITE.
        color_text      Defaults to COLOR_BLACK.
        margin_left     Defaults to 0.
        margin_right    Defaults to 0.
        margin_up       Defaults to 0.
        margin_down     Defaults to 0.
        margin          Write-only, sets all margins.
        color_debug_rect  Just for debugging, defaults to None.
        text_top        Render text above bars, defaults to False.
        Any color with None will ommit rendering.
        """
        self.barcode = barcode
        self.color_on = kwargs.get("color_on", COLOR_BLACK)
        self.color_off = kwargs.get("color_off", None)
        self.color_bg = kwargs.get("color_bg", COLOR_WHITE)
        self.color_margin = kwargs.get("color_margin", COLOR_WHITE)
        self.color_text = kwargs.get("color_text", COLOR_BLACK)
        self.color_debug_rect = kwargs.get("color_debug_rect")
        self.text_top = kwargs.get("text_top", False)
        self.set_margin(kwargs.get("margin", 0.0))
        if "margin_left" in kwargs:
            self.margin_left = kwargs.get("margin_left", 0.0)
        if "margin_right" in kwargs:
            self.margin_right = kwargs.get("margin_right", 0.0)
        if "margin_top" in kwargs:
            self.margin_top = kwargs.get("margin_top", 0.0)
        if "margin_bottom" in kwargs:
            self.margin_bottom = kwargs.get("margin_bottom", 0.0)

    def set_margin(self, margin):
        self.margin_left = margin
        self.margin_right = margin
        self.margin_top = margin
        self.margin_bottom = margin

    def get_margin(self):
        raise NotImplementedError("cannot get general margin")

    margin = property(get_margin, set_margin)

    def has_svg_support(self):
        return False
    
    def get_svg(self, width, height):
        """
        Should return SVG XML as a string.
        """
        raise NotImplementedError()

    def has_png_support(self):
        return False

    def get_png(self, width, height):
        """
        Should return PNG binary data as a string.
        """
        raise NotImplementedError()

    def has_postscript_support(self):
        return False

    def get_postscript(self):
        """
        Should return PostScript data as a string.
        """
        raise NotImplementedError()

    def _save(self, filename, width, height, data_func):
        f = file(filename, "w")
        f.write(data_func(width, height))
        f.close()

    def save_svg(self, filename, width, height):
        self._save(filename, width, height, self.get_svg)
    
    def save_png(self, filename, width, height):
        self._save(filename, width, height, self.get_png)

    def save_postscript(self, filename, width, height):
        self._save(filename, width, height, self.get_postscript)


class CairoRender(Render):
    """
    A rendering type for Cairo.
    """

    def __init__(self, barcode, **kwargs):
        Render.__init__(self, barcode, **kwargs)

    def has_svg_support(self):
        return True

    def write_svg(self, io, width, height):
        surface = cairo.SVGSurface(io, width, height)
        context = cairo.Context(surface)
        self.render_barcode_to_cairo_context(context, 0.0, 0.0, width, height)
        surface.finish()
        return io

    def get_svg(self, width, height):
        io = StringIO.StringIO()
        surface = cairo.SVGSurface(io, width, height)
        context = cairo.Context(surface)
        self.render_barcode_to_cairo_context(context, 0.0, 0.0, width, height)
        surface.finish()
        return io.getvalue()

    def get_png(self, width, height):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        context = cairo.Context(surface)
        self.render_barcode_to_cairo_context(context, 0.0, 0.0, width, height)
        io = StringIO.StringIO()
        surface.write_to_png(io)
        surface.finish()
        return io.getvalue()

    def render_barcode_to_cairo_context(self, context, ax, ay, aw, ah, barcode = None):
        if not barcode:
            barcode = self.barcode
        context.save()
        context.identity_matrix()
        font_options = cairo.FontOptions()
        font_options.set_hint_style(cairo.HINT_STYLE_NONE)
        font_options.set_hint_metrics(cairo.HINT_METRICS_OFF)
        context.reset_clip()
        context.set_font_options(font_options)
        context.rectangle(ax, ay, aw, ah)
        context.clip()
        if self.color_margin:
            self.render_rectangle_to_cairo_context(context, ax, ay, aw, ah, self.color_margin)
        ax += self.margin_left
        ay += self.margin_top
        aw -= (self.margin_right + self.margin_left)
        ah -= (self.margin_bottom + self.margin_top)
        context.reset_clip()
        context.rectangle(ax, ay, aw, ah)
        context.clip()
        if self.color_bg:
            self.render_rectangle_to_cairo_context(context, ax, ay, aw, ah, self.color_bg)
        for index, (bx, by, bw, bh, value) in enumerate(barcode.get_bar_geometries()):
            if self.text_top:
                by = 1.0 - bh
            rx, ry, rw, rh = ax + bx * aw, ay + by * ah, bw * aw, bh * ah
            if value and self.color_on:
                self.render_rectangle_to_cairo_context(context, rx, ry, rw, rh, self.color_on)
            elif not value and self.color_off:
                self.render_rectangle_to_cairo_context(context, rx, ry, rw, rh, self.color_off)
        for index, (bx, by, bw, bh, text) in enumerate(barcode.get_unicode_geometries()):
            if self.text_top:
                by = 0.0
            rx, ry, rw, rh = ax + bx * aw, ay + by * ah, bw * aw, bh * ah
            self.render_text_to_cairo_context(context, rx, ry, rw, rh, text, self.color_text)
        context.restore()

    def render_rectangle_to_cairo_context(self, context, rx, ry, rw, rh, color):
        context.save()
        context.set_source_rgba(*color)
        context.set_line_width(0.0)
        context.rectangle(rx, ry, rw, rh)
        context.fill()
        context.restore()

    def render_text_to_cairo_context(self, context, rx, ry, rw, rh, text, color):
        context.save()
        context.identity_matrix()
        if self.color_debug_rect:
            context.set_line_width(1.0)
            context.set_source_rgba(*self.color_debug_rect)
            context.rectangle(rx, ry, rw, rh)
            context.stroke()
        context.set_source_rgba(*color)
        context.set_font_size(rh * 1.2)
        tx, ty, text_width, text_height = context.text_extents(text)[:4]
        if text_width > rw:
            scalew = rw / float(text_width)
        else:
            scalew = 1.0
        if text_height > rh:
            scaleh = rh / float(text_height)
        else:
            scaleh = 1.0
        context.move_to(rx + rw * 0.5 - text_width * 0.5 * scalew - tx * scalew, ry + rh)
        context.scale(scalew, scaleh)
        context.show_text(text)
        context.stroke()
        context.restore()

