# -*- coding: utf-8 -*-
import cairo, pango


class Style(object):

    def __init__(self, **kwargs):
        self.color = kwargs.get("color", (0.0, 0.0, 0.0))
        self.border_size = kwargs.get("border_size", 0.0)
        self.border_color = kwargs.get("border_color", (0.0, 0.0, 0.0))
        self.border_dash = kwargs.get("border_dash", [])
        self.background_color = kwargs.get("background_color")
        self.background_gradient = kwargs.get("background_gradient")
        self.background_image = kwargs.get("background_image")


DEFAULT_STYLE = Style()


class Packing(object):
    """
    Holds packing information for a child in a box.
    """

    def __init__(self, expand = True, fill = True, halign = 0.5, valign = 0.5):
        self.expand = expand
        self.fill = fill
        self.halign = halign
        self.valign = valign


class TablePacking(object):
    """
    Holds packing information for a table child.
    """
    EXPAND = 0x01
    FILL = 0x02
    EXPAND_AND_FILL = 0x03

    def __init__(self, hoptions = 0, voptions = 0, halign = 0.5, valign = 0.5):
        if hoptions < 0 or hoptions > 3:
            raise ValueError("invalid horizontal options for table packing")
        if voptions < 0 or voptions > 3:
            raise ValueError("invalid vertical options for table packing")
        self.hoptions = hoptions
        self.voptions = voptions
        self.halign = halign
        self.valign = valign


class Area(object):
    """
    Any area occupying space in a layout.
    """

    def __init__(self, **kwargs):
        self.style = kwargs.get("style", Style(**kwargs))
        self._parent = None
        self._left, self._top = 0.0, 0.0
        self._width, self._height = 0.0, 0.0

    def reparent(self, parent, update_parent = True):
        if update_parent and self._parent:
            self._parent.remove(self)
        self._parent = parent
            
    def get_size_request(self):
        raise NotImplementedError("abstract method get_size_request not implemented for type '%s'"%type(self).__name__)

    def set_allocation(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    left = property(lambda o: o._left, lambda o, v: setattr(o, "_left", v))
    top = property(lambda o: o._top, lambda o, v: setattr(o, "_top", v))
    width = property(lambda o: o._width, lambda o, v: setattr(o, "_width", v))
    height = property(lambda o: o._height, lambda o, v: setattr(o, "_height", v))
        
    def get_allocation(self):
        return self._left, self._top, self._width, self._height

    def allocate(self):
        self.set_allocation(self.left, self.top, self.width, self.height)

    def get_inner_rect(self):
        return (self.left + self.style.border_size,
                self.top + self.style.border_size,
                self.width - self.style.border_size * 2.0, 
                self.height - self.style.border_size * 2.0)

    def render(self, context):
        x, y, w, h = self.get_allocation()
        if self.style.background_color:
            context.set_source_rgb(*self.style.background_color)
            context.rectangle(x, y, w, h)
            context.fill()
        if self.style.border_size and self.style.border_color:
            context.set_source_rgb(*self.style.border_color)
            context.set_line_width(self.style.border_size)
            context.set_dash(self.style.border_dash)
            context.rectangle(x + self.style.border_size * 0.5, y + self.style.border_size * 0.5,
                              w - self.style.border_size, h - self.style.border_size)
            context.stroke()



class Container(Area):
    """
    An area that can hold other area's.
    """

    def __init__(self, **kwargs):        
        Area.__init__(self, **kwargs)
        self._children = []

    def __contains__(self, child):
        return child in self._children

    def __len__(self):
        return len(self._children)

    def __iter__(self):
        return iter(self._children)

    def append_many(self, children):
        for child in children:
            self.append(child)

    def append(self, child):
        if not child in self:
            self._children.append(child)
        child.reparent(self, False)

    def remove(self, child):
        self._children.remove(child)
        child.reparent(None, False)

    def insert(self, index, child):
        if child in self:
            self.remove(child)

    def render(self, context):
        Area.render(self, context)
        for child in self:
            child.render(context)


class Box(Container):
    """
    A container with packed children.
    """

    def __init__(self, **kwargs):
        Container.__init__(self, **kwargs)
        self._packing = {}
        self.spacing = kwargs.get("spacing", 0.0)

    def get_packing(self, child):
        return self._packing.get(child, Packing())
    
    def append_many(self, children, expand = True, fill = True, halign = 0.5, valign = 0.5):
        for child in children:
            self.append(child, expand, fill, halign, valign)

    def append(self, child, expand = True, fill = True, halign = 0.5, valign = 0.5):
        Container.append(self, child)
        self._packing[child] = Packing(expand, fill, halign, valign )

    def insert(self, index, child, expand = True, fill = True, halign = 0.5, valign = 0.5):
        Container.insert(self, index, child)
        self._packing[child] = Packing(expand, fill, halign, valign)

    def get_num_expanding(self):
        return sum((1 for child in self if self.get_packing(child).expand))

    def get_expand(self, child):
        if child in self._packing:
            return self._packing[child].expand
        return False

    def set_expand(self, child, value):
        if not child in self._packing:
            self._packing[child] = Packing()
        self._packing[child].expand = value

    def get_fill(self, child):
        if child in self._packing:
            return self._packing[child].fill
        return False

    def set_fill(self, child, value):
        if not child in self._packing:
            self._packing[child] = Packing()
        self._packing[child].fill = value

    def get_halign(self, child):
        if child in self._packing:
            return self._packing[child].halign
        return 0

    def set_halign(self, child, value):
        if not child in self._packing:
            self._packing[child] = Packing()
        self._packing[child].halign = value

    def get_valign(self, child):
        if child in self._packing:
            return self._packing[child].valign
        return 0

    def set_valign(self, child, value):
        if not child in self._packing:
            self._packing[child] = Packing()
        self._packing[child].valign = value

    def get_expandable_space(self, value, ind):
        """
        Returns the space expanding children can use to expand in.
        First argument is either width or height, second value is
        0 for horizontal and 1 for vertical space.
        """
        if self.get_num_expanding() == 0:
            extra = value - self.spacing * len(self) + self.spacing
        else:
            extra = (value
                     - sum((size[ind] for size in (child.get_size_request() for child in self)))
                     - self.spacing * len(self) + self.spacing) / float(self.get_num_expanding())
        return extra


class HBox(Box):
    """
    Horizontal packing of children.
    """

    def get_size_request(self):
        width = 0.0
        height = 0.0
        for child in self:
            cw, ch = child.get_size_request()
            width += cw
            if ch > height:
                height = ch
        return width + self.style.border_size * 2, height + self.style.border_size * 2

    def get_expandable_space(self):
        x, y, w, h = self.get_inner_rect()
        return Box.get_expandable_space(self, w, 0)
            
    def set_allocation(self, left, top, width, height):
        Container.set_allocation(self, left, top, width, height)
        ix, iy, iw, ih = self.get_inner_rect()
        if len(self) > 0:
            extra_space = self.get_expandable_space()
            x = ix
            y = iy
            if extra_space > 0:
                for child in self:
                    cw, ch = child.get_size_request()
                    if self.get_expand(child):
                        if self.get_fill(child):
                            child.set_allocation(x, y, cw + extra_space, ih)
                        else:
                            child.set_allocation(x + (cw + extra_space) * self.get_halign(child)
                                                 - cw * self.get_halign(child),
                                                 y, cw, ih)
                        x += cw + extra_space + self.spacing
                    else:
                        child.set_allocation(x, y, cw, ih)
                        x += cw + self.spacing
            else:
                for child in self:
                    cw, ch = child.get_size_request()
                    child.set_allocation(x, y, cw, ih)
                    x += cw + self.spacing


class VBox(Box):
    """
    Vertical packing of children.
    """

    def get_size_request(self):
        width = 0.0
        height = 0.0
        for child in self:
            cw, ch = child.get_size_request()
            height += ch
            if cw > width:
                width = cw
        return width + self.style.border_size * 2, height + self.style.border_size * 2

    def get_expandable_space(self):
        x, y, w, h = self.get_inner_rect()
        return Box.get_expandable_space(self, h, 1)

    def set_allocation(self, left, top, width, height):
        Container.set_allocation(self, left, top, width, height)
        ix, iy, iw, ih = self.get_inner_rect()
        if len(self) > 0:
            extra_space = self.get_expandable_space()
            x = ix
            y = iy
            if extra_space > 0:
                for child in self:
                    cw, ch = child.get_size_request()
                    if self.get_expand(child):
                        if self.get_fill(child):
                            child.set_allocation(x, y, iw, ch + extra_space)
                        else:
                            child.set_allocation(x,
                                                 y + (ch + extra_space) * self.get_valign(child)
                                                 - ch  * self.get_valign(child),
                                                 iw, ch)
                        y += ch + extra_space + self.spacing
                    else:
                        child.set_allocation(x, y, iw, ch)
                        y += ch + self.spacing
            else:
                for child in self:
                    cw, ch = child.get_size_request()
                    child.set_allocation(x, y, iw, ch)
                    y += ch + self.spacing
                    
                

class Table(Container):
    """
    A table adds a coordinate system for the container.
    """

    def __init__(self, **kwargs):
        Container.__init__(self, **kwargs)
        self._packing = {}
        self._cells = {}

    def append_many(self, children):
        raise NotImplementedError("Table doesn't allow append_many operations")

    def append(self, child):
        raise NotImplementedError("Table doesn't allow append operations")

    def insert(self, index, child):
        raise NotImplementedError("Table doesn't allow insert operations")

    def get_packing(self, child):
        return self._packing.get(child, TablePacking())
    
    def set_cell(self, child, left, top, width, height,
                 hoptions = TablePacking.EXPAND_AND_FILL,
                 voptions = TablePacking.EXPAND_AND_FILL,
                 halign = 0.5, valign = 0.5):
        Container.append(self, child)
        self._cells[child] = (left, top, width, height)
        self._packing[child] = TablePacking(hoptions, voptions, halign, valign)

    def get_cell(self, left, top):
        return self._cells.get((left, top))

    def clear_cell(self, left, top):
        self.remove(self.get_cell(left, top))

    def remove(self, child):
        if child and child in self:
            Container.remove(self, child)
            if child in self._packing:
                del self._packing[child]
            if child in self._cells:
                del self._cells[child]

    def set_hflag(self, child, value, flag):
        if flag < 0 or flag > 3:
            raise ValueError("invalid horizontal options for table packing")
        if not child in self._packing:
            self._packing[child] = Packing()
        if value:
            self._packing[child].hoptions |= flag
        else:
            self._packing[child].hoptions &= (0xff - flag)

    def set_vflag(self, child, value, flag):
        if flag < 0 or flag > 3:
            raise ValueError("invalid vertical options for table packing")
        if not child in self._packing:
            self._packing[child] = Packing()
        if value:
            self._packing[child].voptions |= flag
        else:
            self._packing[child].voptions &= (0xff - flag)

    def set_hexpand(self, child, value):
        self.set_hflag(child, value, TablePacking.EXPAND)

    def get_hexpand(self, child, value):
        return self.get_packing(child).hoptions & TablePacking.EXPAND

    def set_hfill(self, child, value):
        self.set_hflag(child, value, TablePacking.FILL)

    def get_hfill(self, child, value):
        return self.get_packing(child).hoptions & TablePacking.FILL

    def set_vexpand(self, child, value):
        self.set_vflag(child, value, TablePacking.EXPAND)

    def get_vexpand(self, child, value):
        return self.get_packing(child).voptions & TablePacking.EXPAND

    def set_vfill(self, child, value):
        self.set_vflag(child, value, TablePacking.FILL)

    def get_vfill(self, child, value):
        return self.get_packing(child).voptions & TablePacking.FILL

    def get_halign(self, child):
        if child in self._packing:
            return self._packing[child].halign
        return 0

    def set_halign(self, child, value):
        if not child in self._packing:
            self._packing[child] = Packing()
        self._packing[child].halign = Value

    def get_valign(self, child):
        if child in self._packing:
            return self._packing[child].valign
        return 0

    def set_valign(self, child, value):
        if not child in self._packing:
            self._packing[child] = Packing()
        self._packing[child].valign = Value

    def get_geom_for_child(self, child):
        if child in self._cells:
            return self._cells[child]
        raise ValueError("child not found in table")

    def get_column_count(self):
        width = 0
        for x, y, w, h in self._cells.values():
            if x + w > width:
                width = x + w
        return width

    def get_row_count(self):
        height = 0
        for x, y, w, h in self._cells.values():
            if y + h > height:
                height = y + h
        return height

    def get_size_request(self):
        raise NotImplementedError("no idea how this is going to be implemented")

    def set_allocation(self, left, top, width, height):
        Container.set_allocation(self, left, top, width, height)
        raise NotImplementedError("no idea how this is going to be implemented")


class Fixed(Container):
    
    def __init__(self, **kwargs):
        Container.__init__(self, **kwargs)
        self._geometries = {}

    def append_many(self, child):
        raise NotImplementedError("Fixed containers do not support append_many")

    def insert(self, child):
        raise NotImplementedError("Fixed containers do not support insert")

    def append(self, child, x, y, w = None, h = None):
        Container.append(self, child)
        if w is None:
            w = child.get_size_request()[0]
        if h is None:
            h = child.get_size_request()[1]
        self._geometries[child] = x, y, w, h

    def remove(self, child):
        Container.remove(self, child)
        if child in self._geometries:
            del self._geometries[child]

    def get_geom_for_child(self, child):
        if child in self._geometries:
            return self._geometries[child]
        raise ValueError("child not in Fixed container, unable to get geoms")

    def get_size_request(self):
        width, height = 0.0, 0.0
        for child in self:
            x, y, w, h = self.get_geom_for_child(child)
            if x + w > width:
                width = x + w
            if y + h > height:
                height = y + h
        return width + self.style.border_size * 2, height + self.style.border_size * 2

    def set_allocation(self, left, top, width, height):
        Container.set_allocation(self, left, top, width, height)
        ix, iy, iw, ih = self.get_inner_rect()
        for child in self:
            x, y, w, h = self.get_geom_for_child(child)
            child.set_allocation(ix + x, iy + y, w, h)


class Text(Area):

    def __init__(self, text, size = 12, **kwargs):
        Area.__init__(self, **kwargs)
        self.text = unicode(text)
        self.h_justify = kwargs.get("h_justify", 0.5)
        self.v_justify = kwargs.get("v_justify", 0.5)        
        self._context = cairo.Context(cairo.ImageSurface(cairo.FORMAT_A1, 1, 1))
        self._context.set_font_size(size)

    size = property(lambda o: o._context.get_font_size(), lambda o, v: self._context.set_font_size(v))

    def get_size_request(self):        
        width, height = self._context.text_extents(self.text)[2:4]
        return width + self.style.border_size * 2, height + self.style.border_size * 2

    def render(self, context):
        Area.render(self, context)
        tx, ty, tw, th = context.text_extents(self.text)[:4]
        context.move_to(self.left + self.width * self.h_justify - tw * self.h_justify,
                        self.top - ty + self.height * self.v_justify - th * self.v_justify)
        context.show_text(self.text)


class Image(Area):

    def __init__(self, filename_or_image_surface, **kwargs):
        Area.__init__(self, **kwargs)
        self.image = (isinstance(filename_or_image_surface, basestring)
                      and cairo.ImageSurface.create_from_png(filename_or_image_surface)
                      or filename_or_image_surface)
        self.stretch = kwargs.get("stretch", False)
        
    def get_size_request(self):        
        width, height = self.image.get_width(), self.image.get_height()
        return width + self.style.border_size * 2, height + self.style.border_size * 2

    def render(self, context):
        Area.render(self, context)
        context.save()
        if self.stretch:
            context.translate(self.left + self.style.border_size, self.top + self.style.border_size)
            usable_width = self.width - self.style.border_size * 2.0
            scalex = self.image.get_width() / usable_width
            usable_height = self.height - self.style.border_size * 2.0
            scaley = self.image.get_height() / usable_height
            context.scale(1.0 / scalex, 1.0 / scaley)
        else:
            context.translate(self.left + self.style.border_size
                              + (self.width - self.style.border_size * 2) * 0.5 - self.image.get_width() * 0.5,
                              self.top + self.style.border_size
                              + (self.height - self.style.border_size * 2) * 0.5 - self.image.get_height() * 0.5
                              )            
        context.set_source_surface(self.image, 0, 0)
        context.paint()
        context.restore()
        

