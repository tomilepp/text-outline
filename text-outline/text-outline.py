#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (c) Tomi Leppikangas 2025
#
#    This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

gi.require_version("GimpUi", "3.0")
from gi.repository import GimpUi

gi.require_version("Gegl", "0.4")
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib

import sys


class Outline(Gimp.PlugIn):
    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if len(drawables) != 1:
            msg = "Procedure '{}' only works with one drawable.".format(
                procedure.get_name()
            )
            error = GLib.Error.new_literal(Gimp.PlugIn.error_quark(), msg, 0)
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, error)
        else:
            drawable = drawables[0]

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("text-outline")

            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CANCEL, GLib.Error()
                )
            else:
                dialog.destroy()

        font_color = config.get_property("font_color")
        background_color = config.get_property("background_color")
        text = config.get_property("text")
        font = config.get_property("font")

        Gimp.context_push()
        image.undo_group_start()

        Gimp.context_set_foreground(font_color)
        text_layer = Gimp.TextLayer.new(image, text, font, 100, Gimp.Unit.pixel())

        image.insert_layer(text_layer, None, 0)
        path = Gimp.Path.new_from_text_layer(image, text_layer)
        image.insert_path(path, None, 0)
        image.select_item(Gimp.ChannelOps.ADD, path)

        sel = image.get_selection()
        sel.grow(image, 10)

        width = text_layer.get_width()
        height = text_layer.get_height()
        offset_x, offset_y = text_layer.get_offsets()[1:]
        outline_layer = Gimp.Layer.new(
            image,
            "text outline",
            width,
            height,
            Gimp.ImageType.RGBA_IMAGE,
            100,
            Gimp.LayerMode.NORMAL,
        )
        image.insert_layer(outline_layer, None, 1)
        image.set_selected_layers([outline_layer])
        Gimp.context_set_foreground(background_color)
        outline_layer.edit_fill(0)

        Gimp.displays_flush()

        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, "gimp30-python", None

    def do_query_procedures(self):
        return ["plug-in-text-outline"]

    def do_create_procedure(self, name):
        Gegl.init(None)
        _font_color = Gegl.Color.new("black")
        _background_color = Gegl.Color.new("white")

        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )

        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)

        procedure.set_menu_label("Text Outline Plugin")
        procedure.set_icon_name(GimpUi.ICON_GEGL)
        procedure.add_menu_path("<Image>/Filters/Omat/")

        procedure.set_documentation("Text Outline Plugin", "Text Outline Plugin", name)
        procedure.set_attribution("Tomi", "Tomi", "2025")
        procedure.add_color_argument(
            "font_color",
            "_Font Color",
            "Font Color",
            True,
            _font_color,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_color_argument(
            "background_color",
            "_Background Color",
            "Background Color",
            True,
            _background_color,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_string_argument(
            "text", "_Text", "Text", "Hello World", GObject.ParamFlags.READWRITE
        )
        procedure.add_font_argument(
            "font",
            "Font",
            "Font",
            False,
            Gimp.Font.get_by_name("Serif"),
            True,
            GObject.ParamFlags.READWRITE,
        )

        return procedure


Gimp.main(Outline.__gtype__, sys.argv)
