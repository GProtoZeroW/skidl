﻿from __future__ import print_function
import re

import wx
import wx.grid
import wx.lib.agw.hyperlink as hl

from skidl import search_libraries

APP_TITLE = "SKiDL Part Search"

APP_EXIT = 1
SHOW_HELP = 4
SHOW_ABOUT = 5
SEARCH_PARTS = 6
COPY_PART = 7

APP_SIZE = (600, 500)
BTN_SIZE = (50, -1)
SPACING = 10
TEXT_BOX_WIDTH = 200


class SkidlPartSearch(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(SkidlPartSearch, self).__init__(*args, **kwargs)

        self.InitUI()

    def InitUI(self):

        self.InitMenus()
        self.InitMainPanels()

        self.SetSize(APP_SIZE)
        self.SetTitle(APP_TITLE)
        self.Center()
        self.Show(True)

    def InitMainPanels(self):
        # Main panel holds two subpanels.
        main_panel = wx.Panel(self)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        main_panel.SetSizer(hbox)

        # Subpanel for search text box and lib/part table.
        search_panel = self.InitSearchPanel(main_panel)
        hbox.Add(search_panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=SPACING)

        # Divider.
        hbox.Add(
            wx.StaticLine(main_panel, size=(2, -1), style=wx.LI_VERTICAL),
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=0,
        )

        # Subpanel for part/pin data.
        part_panel = self.InitPartPanel(main_panel)
        hbox.Add(part_panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=0)

    def InitSearchPanel(self, parent):
        # Subpanel for search text box and lib/part table.
        search_panel = wx.Panel(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        search_panel.SetSizer(vbox)

        # Text box for part search string.
        self.search_text = wx.TextCtrl(
            search_panel, size=(TEXT_BOX_WIDTH, -1), style=wx.TE_PROCESS_ENTER
        )
        self.search_text.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        tip = wx.ToolTip("Enter text or regular expression to select parts.")
        self.search_text.SetToolTip(tip)

        # Button to initiate search for parts containing search string.
        search_btn = wx.Button(search_panel, label="Search", size=BTN_SIZE)
        search_btn.Bind(wx.EVT_BUTTON, self.OnSearch)
        tip = wx.ToolTip("Search for parts containing the text or regular expression.")
        search_btn.SetToolTip(tip)

        # Table (grid) for holding libs and parts that match search string.
        self.found_parts = wx.grid.Grid()
        self.found_parts.Create(search_panel)
        self.found_parts.CreateGrid(
            numRows=10, numCols=2, selmode=wx.grid.Grid.SelectRows
        )
        self.found_parts.HideRowLabels()
        self.found_parts.EnableEditing(False)
        self.found_parts.SetColLabelValue(0, "Library")
        self.found_parts.SetColLabelValue(1, "Part")
        self.found_parts.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)

        # Button to copy selected lib/part to clipboard.
        copy_btn = wx.Button(search_panel, label="Copy", size=BTN_SIZE)
        copy_btn.Bind(wx.EVT_BUTTON, self.OnCopy)
        tip = wx.ToolTip("Copy the selected library and part to the clipboard.")
        copy_btn.SetToolTip(tip)

        # Grid for arranging text box, grid and buttons.
        fgs = wx.FlexGridSizer(rows=2, cols=2, vgap=SPACING, hgap=SPACING)
        fgs.AddMany(
            [
                search_btn,
                (self.search_text, 1, wx.EXPAND),
                copy_btn,
                (self.found_parts, 1, wx.EXPAND),
            ]
        )
        fgs.AddGrowableCol(1, 1)  # widths of text box and grid are adjustable.
        fgs.AddGrowableRow(1, 1)  # height of grid is adjustable.

        vbox.Add(fgs, proportion=1, flag=wx.ALL | wx.EXPAND, border=0)

        return search_panel

    def InitPartPanel(self, parent):
        # Subpanel for part/pin data.
        part_panel = wx.Panel(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        part_panel.SetSizer(vbox)

        # Text box for displaying discription of part highlighted in grid.
        vbox.Add(
            wx.StaticText(part_panel, label="Part Description"),
            proportion=0,
            flag=wx.ALL,
            border=SPACING,
        )
        self.part_desc = wx.TextCtrl(
            part_panel,
            size=(TEXT_BOX_WIDTH, 60),
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL,
        )
        vbox.Add(self.part_desc, proportion=0, flag=wx.ALL | wx.EXPAND, border=SPACING)

        # Hyperlink for highlighted part datasheet.
        vbox.Add(
            wx.StaticLine(part_panel, size=(-1, 2), style=wx.LI_HORIZONTAL),
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=5,
        )
        self.datasheet_link = hl.HyperLinkCtrl(part_panel, label="Datasheet", URL="")
        self.datasheet_link.EnableRollover(True)
        vbox.Add(self.datasheet_link, proportion=0, flag=wx.ALL, border=SPACING)

        # Divider.
        vbox.Add(
            wx.StaticLine(part_panel, size=(-1, 2), style=wx.LI_HORIZONTAL),
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=5,
        )

        # Table (grid) of part pin numbers, names, I/O types.
        vbox.Add(
            wx.StaticText(part_panel, label="Pin List"),
            proportion=0,
            flag=wx.ALL,
            border=SPACING,
        )
        self.pin_info = wx.grid.Grid()
        self.pin_info.Create(part_panel)
        self.pin_info.CreateGrid(
            numRows=SPACING, numCols=3, selmode=wx.grid.Grid.SelectRows
        )
        self.pin_info.HideRowLabels()
        self.pin_info.EnableEditing(False)
        self.pin_info.SetColLabelValue(0, "Pin")
        self.pin_info.SetColLabelValue(1, "Name")
        self.pin_info.SetColLabelValue(2, "Type")
        vbox.Add(self.pin_info, proportion=1, flag=wx.ALL | wx.EXPAND, border=SPACING)

        return part_panel

    def InitMenus(self):

        # Top menu.
        menuBar = wx.MenuBar()

        # File submenu containing quit button.
        fileMenu = wx.Menu()
        menuBar.Append(fileMenu, "&File")

        quitMenuItem = wx.MenuItem(fileMenu, APP_EXIT, "Quit\tCtrl+Q")
        fileMenu.Append(quitMenuItem)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=APP_EXIT)

        # Search submenu containing search and copy buttons.
        srchMenu = wx.Menu()
        menuBar.Append(srchMenu, "&Search")

        srchMenuItem = wx.MenuItem(srchMenu, SEARCH_PARTS, "Search\tCtrl+F")
        srchMenu.Append(srchMenuItem)
        copyMenuItem = wx.MenuItem(srchMenu, COPY_PART, "Copy\tCtrl+C")
        srchMenu.Append(copyMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSearch, id=SEARCH_PARTS)
        self.Bind(wx.EVT_MENU, self.OnCopy, id=COPY_PART)

        # Help menu containing help and about buttons.
        helpMenu = wx.Menu()
        menuBar.Append(helpMenu, "&Help")

        helpMenuItem = wx.MenuItem(helpMenu, SHOW_HELP, "Help\tCtrl+H")
        helpMenu.Append(helpMenuItem)
        aboutMenuItem = wx.MenuItem(helpMenu, SHOW_ABOUT, "About App\tCtrl+A")
        helpMenu.Append(aboutMenuItem)
        self.Bind(wx.EVT_MENU, self.ShowHelp, id=SHOW_HELP)
        self.Bind(wx.EVT_MENU, self.ShowAbout, id=SHOW_ABOUT)

        self.SetMenuBar(menuBar)

    def OnSearch(self, event):
        # Scan libraries looking for parts that match search string.
        self.lib_parts = set()
        lib_part_iter = search_libraries(self.search_text.GetLineText(0))
        progress = wx.ProgressDialog(
            "Searching Part Libraries", "Loading parts from libraries."
        )
        for lib_part in lib_part_iter:
            if lib_part[0] == "LIB":
                lib_name = lib_part[1]
                lib_idx = lib_part[2]
                total_num_libs = lib_part[3]
                progress.SetRange(total_num_libs)
                progress.Update(lib_idx, "Reading library {}...".format(lib_name))
            elif lib_part[0] == "PART":
                lib_name = lib_part[1]
                part = lib_part[2]
                self.lib_parts.add((lib_name, part))

        # Sort parts by libraries and part names.
        self.lib_parts = sorted(
            list(self.lib_parts), key=lambda x: "/".join([x[0], x[1].name])
        )

        # place libraries and parts into a table.
        grid = self.found_parts

        # Clear any existing grid cells and add/sub rows to hold search results.
        grid.ClearGrid()
        num_rows_chg = len(self.lib_parts) - grid.GetNumberRows()
        if num_rows_chg < 0:
            grid.DeleteRows(0, -num_rows_chg, True)
        elif num_rows_chg > 0:
            grid.AppendRows(num_rows_chg)

        # Places libs and part names into table.
        for row, (lib, part) in enumerate(self.lib_parts):
            grid.SetCellValue(row, 0, lib)
            grid.SetCellValue(row, 1, part.name)

        # Size the columns for their new contents.
        grid.AutoSizeColumns()

    def OnSelectCell(self, event):
        # When a row of the lib/part table is selected, display the data for that part.

        def natural_sort_key(s, _nsre=re.compile("([0-9]+)")):
            return [
                int(text) if text.isdigit() else text.lower() for text in _nsre.split(s)
            ]

        # Get any selected rows in the lib/part table plus wherever the cell cursor is.
        selection = self.found_parts.GetSelectedRows()
        selection.append(self.found_parts.GetGridCursorRow())

        # Only process the part in the first selected row and ignore the rest.
        for row in selection:
            # Fully instantiate the selected part.
            part = self.lib_parts[row][1]
            part.parse()  # Instantiate pins.

            # Show the part description.
            part_desc = self.part_desc
            part_desc.Remove(0, part_desc.GetLastPosition())
            part_desc.WriteText(part.description)

            # Display the link to the part datasheet.
            self.datasheet_link.SetURL(part.datasheet)

            # Place pin data into a table.
            grid = self.pin_info

            # Clear any existing pin data and add/sub rows to hold results.
            grid.ClearGrid()
            num_rows_chg = len(part) - grid.GetNumberRows()
            if num_rows_chg < 0:
                grid.DeleteRows(0, -num_rows_chg, True)
            elif num_rows_chg > 0:
                grid.AppendRows(num_rows_chg)

            # Sort pins by pin number.
            pins = sorted(part, key=lambda p: natural_sort_key(p.get_pin_info()[0]))

            # Place pin data into the table.
            for row, pin in enumerate(pins):
                num, names, func = pin.get_pin_info()
                grid.SetCellValue(row, 0, num)
                grid.SetCellValue(row, 1, names)
                grid.SetCellValue(row, 2, func)

            # Size the columns for their new contents.
            grid.AutoSizeColumns()

            # Return after processing only one part.
            return

    def OnCopy(self, event):
        # Copy the lib/part for the selected part onto the clipboard.

        # Get any selected rows in the lib/part table plus wherever the cell cursor is.
        selection = self.found_parts.GetSelectedRows()
        selection.append(self.found_parts.GetGridCursorRow())

        # Only process the part in the first selected row and ignore the rest.
        for row in selection:
            # Deselect all rows but the first.
            self.found_parts.SelectRow(row)

            # Create a SKiDL part instantiation.
            lib = self.found_parts.GetCellValue(row, 0)
            part = self.found_parts.GetCellValue(row, 1)
            part_inst = "Part(lib='{lib}', name='{part}')".format(lib=lib, part=part)

            # Make a data object to hold the SKiDL part instantiation.
            dataObj = wx.TextDataObject()
            dataObj.SetText(part_inst)

            # Place the SKiDL part instantiation on the clipboard.
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(dataObj)
                wx.TheClipboard.Flush()
            else:
                Feedback("Unable to open clipboard!", "Error")
            return

    def Feedback(self, msg, label):
        dlg = wx.MessageDialog(self, msg, label, wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def ShowHelp(self, e):
        self.Feedback(
            """
1. Enter text to search for in the part descriptions.
2. Start the search by pressing Return or clicking on the Search button.
3. Matching parts will appear in the lib/part table in the left-hand pane.
4. Select a row in the lib/part table to display part info in the right-hand pane.
5. Click the Copy button to place the selected library and part on the clipboard.
6. Paste the clipboard contents into your SKiDL code.
            """,
            "Help",
        )

    def ShowAbout(self, e):
        self.Feedback(
            APP_TITLE
            + """
(c) 2019 XESS Corp.
https://github.com/xesscorp/skidl
MIT License
            """,
            "About",
        )

    def OnQuit(self, e):
        self.Close()


def main():

    ex = wx.App()
    SkidlPartSearch(None)
    ex.MainLoop()


if __name__ == "__main__":
    main()