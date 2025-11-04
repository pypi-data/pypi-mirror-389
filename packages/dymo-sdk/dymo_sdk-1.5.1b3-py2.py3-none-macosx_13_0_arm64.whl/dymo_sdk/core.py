"""Provides functionality for interacting with Dymo Labels

This package provides a python wrapper around the .NET SDK for DYMO Printers and Labels.
"""
import pythonnet
import os
from pythonnet import load
import clr_loader
import asyncio
from packaging.version import Version
from enum import Enum
from enum import auto
import sys
import shutil
import glob
import platform

__all__ = [
    "LabelObject",
    "DymoLabel",
    "DymoPrinter",
    "RollStatus",
    "get_printers",
    "print_label",
    "is_roll_status_supported",
    "refresh_printer",
    "get_roll_status"
]

#load the Desktop .Net core to help ensure functionality
__specToLoad = ""
__spec_ver = "0"
for r in clr_loader.find_runtimes():
    if platform.system() == "Windows":
        if r.name == "Microsoft.WindowsDesktop.App" and Version(r.version) >= Version(__spec_ver):
            __specToLoad = r
            __spec_ver = r.version
    else:
        if r.name == "Microsoft.NETCore.App" and r.version[0] == "8":
            __specToLoad = r
            __spec_ver = r.version
if __specToLoad != "":
    clr_instance = clr_loader.get_coreclr(runtime_spec=__specToLoad)
    load(clr_instance)
else:
    load("coreclr")

import clr
import System

__curr_dir = os.path.dirname(os.path.abspath(__file__))
__dlls_dir = os.path.join((__curr_dir), "dlls")

#This section is to copy the appropriate files
#Note: You can remove this code section in the actual package
#if platform.system() == "Windows":
#    __p_dir = root_dir=os.path.join((__curr_dir), "dlls/Win")
#else: #if not windows, add mac and hope it's compatible with windows
#    __p_dir = root_dir=os.path.join((__curr_dir), "dlls/Mac")
#__dlls = glob.glob("*", root_dir=__p_dir)
#for __dll in __dlls:
#    if os.path.isdir(__p_dir + "/" + __dll):
#        if os.path.exists(__dlls_dir + "/" + __dll):
#            shutil.rmtree(__dlls_dir + "/" + __dll)
#        shutil.copytree(__p_dir + "/" + __dll, __dlls_dir + "/" + __dll)
#    else:    
#        shutil.copy(__p_dir + "/" + __dll, __dlls_dir)

sys.path.append(__dlls_dir)

clr.AddReference('DymoSDK')
clr.AddReference('Dymo.LabelAPI')

#to allow debugger to attach if needed
#__test = input("press enter to continue")

import DymoSDK

from DymoSDK.Implementations import DymoPrinter as NativeDymoPrinter
from DymoSDK.Implementations import DymoLabel as NativeDymoLabel
from DymoSDK import App
from System import Convert
import DYMO.LabelAPI
from DymoSDK.Interfaces import IPrinter
App.Init() #where should this be run?
__printer_manager = NativeDymoPrinter.Instance

class LabelObjectType(Enum):
    """An ENUM representing the type of object."""
    TEXT = auto()
    ADDRESS = auto()
    COUNTER = auto()
    BARCODE = auto()
    QRCODE = auto()
    IMAGE = auto()
    #Types that cannot be updated
    SHAPE = auto()
    NONE = auto()

class LabelObject:
    """An object on a label, such as Text, Barcode, etc. Should not be explicitly constructed.
    
    Attributes:
        native: The native C# label object, should not be needed for the average user.
        owner: The DymoLabel instance that this object is attached to.
        object_type: The type of object this label is.
    """
    _typeDict = {
        "TextObject" : LabelObjectType.TEXT,
        "AddressObject" : LabelObjectType.ADDRESS,
        "CounterObject" : LabelObjectType.COUNTER,
        "BarcodeObject" : LabelObjectType.BARCODE,
        "QRCodeObject" : LabelObjectType.QRCODE,
        "ImageObject" : LabelObjectType.IMAGE,
        "ShapeObject" : LabelObjectType.SHAPE,
        "None" : LabelObjectType.NONE
    } 

    def __init__(self, native_label_object, label):
        """Creates a Python LabelObject from a C# LabelObject."""
        self.native = native_label_object
        self.object_type = LabelObject._typeDict[native_label_object.Type.ToString()]
        self.owner = label
    
    @property
    def name(self):
        """The name of the label object."""
        return self.native.Name
    @name.setter
    def name(self, new_name):
        self.owner._nameToPythonMap[new_name] = self
        self.owner._nameToPythonMap.pop(self.native.Name, None)
        self.native.Name = new_name
    
    
    def update_data(self, new_value: str):
        """Updates the current data using the new_value as a String."""
        return self.owner.native.UpdateLabelObject(self.native, new_value)
    
    def update_image_data_from_file(self, filepath: str):
        """If this object is an image object, updates the image data using the file provided."""
        if self.object_type != LabelObjectType.IMAGE:
            raise TypeError("You cannot call update_image_data_from_file on a non image object.")
        
        return self.owner.native.SetImageFromFilePath(self.name, filepath)


    
    

class DymoLabel:
    """A Dymo Label object.
    
    Attributes:
        :native: The underlying DymoLabel object from C#.
    """

    def __init__(self, *, filepath: str ="", xml: str =""):
        """Initializes the Label Object, optionally from a file or XML string.

        Args:
            :filepath (str): The path to a .dymo or .label file to load the label from.
            :xml (str): An XML string to load the label from.
        """

        #WARNING: This is deprecated and will need to be changed in the future
        self.native = NativeDymoLabel.Instance
        self._nameToPythonMap = {}
    
        if filepath != "":
            self.native.LoadLabelFromFilePath(filepath)
        elif xml != "":
            utf8Bom = '\ufeff'
            if xml.startswith(utf8Bom):
                xml = xml[len(utf8Bom):]
            self.native.LoadLabelFromXML(xml)
    
    def load_label_from_xml(self, xml: str):
        """Loads a label from an XML String.

        Args:
            :xml (str): An XML String describing a Dymo label.
        """
        utf8Bom = '\ufeff'
        if xml.startswith(utf8Bom):
            xml = xml[len(utf8Bom):]
        self.native.LoadLabelFromXML(xml)
    
    def load_label_from_file(self, filepath: str):
        """Loads a label from a .dymo, .label, or .xml file.

        Args:
            :filepath (str): the path to the file
        """
        self.native.LoadLabelFromFilePath(filepath)

    def get_label_objects(self):
        """Returns a list of LabelObjects on the Label."""
        result_list = []
        nativeLabelObjects = self.native.GetLabelObjects()
        for lo in nativeLabelObjects:
            if lo.Name in self._nameToPythonMap:
                result_list.append(self._nameToPythonMap[lo.Name])
            else:
                new_label_object = LabelObject(lo, self)
                self._nameToPythonMap[new_label_object.name] = new_label_object
                result_list.append(new_label_object)
        
        return result_list
    
    def get_label_object(self, obj_name: str):
        """Returns the Label Object from the given obj_name, or none if it does not exist."""
        label_obj = self.native.GetLabelObject(obj_name)
        if label_obj == None:
            return None
        if label_obj.Name in self._nameToPythonMap:
            return self._nameToPythonMap[label_obj.Name]
        new_label_obj = LabelObject(label_obj, self)
        return new_label_obj

    def update_label_object(self, label_obj: LabelObject, new_value: str):
        """Updates the given label object on this label with the new value.

        Updates the label object of this label if found. If label_obj's owner is the same as this current label, then provides duplicate functionality of label_obj.update_data().
        """
        return self.native.UpdateLabelObject(label_obj.native, new_value)
    
    def get_preview_label(self) -> str:
        """Returns a preview of the current label.
        
        Returns the current label as an image by a base64 string. 
        """
        return Convert.ToBase64String(self.native.GetPreviewLabel())
    
    def update_image_object_from_file(self, label_obj: LabelObject | str, filepath: str):
        """Updates an image object using the given filepath.

        Args:
            :label_obj: Either LabelObject Instance or the name of such an instance.
            :filepath (str): the path to the file.
        """
        if type(label_obj) == LabelObject:
            return self.native.SetImageFromFilePath(label_obj.name, filepath)
        elif type(label_obj) == str:
            return self.native.SetImageFromFilePath(label_obj, filepath)
        else:
            raise TypeError("label_obj must be a string or LabelObject instance!")
    
    def save(self, filepath: str):
        """Saves this label to the specified file path."""
        self.native.Save(filepath)


class RollStatus:
    """A class that represents the roll status.

    Attributes:
        :sku: (str) the SKU of the roll.
        :name: (str) the name of the roll.
        :labels_remaining: (int) the number of labels remaining in the detected roll.
        :RollStatus: (str) The status of the roll.
    """
    def __init__(self, native):
        self.native = native
        self.sku = native.SKU
        self.name = native.Name
        self.labels_remaining = native.LabelsRemaining
        self.roll_status = native.RollStatus

class DymoPrinter:
    """A class representing Dymo Printers. Should not be constructed directly but instead found through get_printers()."""
    _name_to_python_dict = {}
    __printer_manager = NativeDymoPrinter.Instance
    def __init__(self, native):
        """Initializes a dymo printer."""
        self.native = native
    @property
    def name(self):
        return self.native.Name
    @property
    def driver_name(self):
        return self.native.DriverName
    @property
    def is_twin_turbo(self):
        return self.native.IsTwinTurbo
    @property
    def is_local(self):
        return self.native.IsLocal
    @property
    def is_connected(self):
        return self.native.IsConnected
    @property
    def is_auto_cut_supported(self):
        return self.native.IsAutoCutSupported
    @property
    def printer_type(self):
        return self.native.PrinterType
    
    def is_roll_status_supported(self) -> bool:
        """Returns if this printer belongs to the 550 series."""
        return DymoPrinter.__printer_manager.IsRollStatusSupported(self.name)
    
    def get_roll_status(self) -> RollStatus:
        """Returns roll status."""
        return RollStatus(DymoPrinter.__printer_manager.GetRollStatusInPrinter(self.name).Result)

    def print_label(self, label: DymoLabel, copies: int = 1, collate: bool = False, mirror: bool = False, roll_selected: int = 0, chain_marks: bool = False, barcode_graphics_quality: bool = False):
        """Prints the given label on this printer

        Args:
            :label: A DymoLabel instance to print.
            :copies: The number of copies to print.
            :collate: Whether or not the print job should be collated.
            :mirror: Whether or not the print job should be mirrored.
            :roll_selected: On Twin Turbo 450 Printers you can specify which port to print out of. 0 is auto, and 1 is left, and 2 is right.
            :chain_marks: On D1 Printers places markings between labels.
            :barcode_graphics_quality: Enables higher quality printing to help ensure barcode quality. Can lead to slower print jobs.
        """
    
        return DymoPrinter.__printer_manager.PrintLabel(label.native, self.name, copies, collate, mirror, roll_selected, chain_marks, barcode_graphics_quality)

    def refresh_connection(self):
        """Refreshes the printer connection. 
        
        Note that this is done asynchronously and we recommend sleeping for 0.1 seconds if the results are required immediately.
        """
        DymoPrinter.__printer_manager.GetPrinterStatus(self.name)

    
def get_printers() -> list[DymoPrinter]:
    """Returns a list of DymoPrinter objects."""
    printers = __printer_manager.GetPrinters()
    printers = System.Collections.Generic.List[IPrinter](printers)
    res = []
    for p in printers:
        #if(p.Name in DymoPrinter._name_to_python_dict):
        #    new_p = DymoPrinter(p.Name, p.DriverName, p.IsTwinTurbo, p.IsLocal, p.IsConnected, p.IsAutoCutSupported, p.PrinterType)
        #    DymoPrinter._name_to_python_dict[p.Name] = new_p
        #    res.append(DymoPrinter._name_to_python_dict[p.Name])
        #else:
        new_p = DymoPrinter(p)
        DymoPrinter._name_to_python_dict[p.Name] = new_p
        res.append(new_p)
    return res

def print_label(label: DymoLabel, printer: DymoPrinter | str, copies: int = 1, collate: bool = False, mirror: bool = False, roll_selected: int = 0, chain_marks: bool = False, barcode_graphics_quality: bool = False):
    """Prints the given label on the specified printer asynchronously.
    
    Args:
        :label: A DymoLabel instance to print.
        :printer: The DymoPrinter to print it from. Can be a DymoPrinter instance or just the name.
        :copies: The number of copies to print.
        :collate: Whether or not the print job should be collated.
        :mirror: Whether or not the print job should be mirrored.
        :roll_selected: On Twin Turbo 450 Printers you can specify which port to print out of. 0 is auto, and 1 is left, and 2 is right.
        :chain_marks: On D1 Printers places markings between labels.
        :barcode_graphics_quality: Enables higher quality printing to help ensure barcode quality. Can lead to slower print jobs.
    """
    if type(printer) is DymoPrinter:
        printer = printer.name
    
    return __printer_manager.PrintLabel(label.native, printer, copies, collate, mirror, roll_selected, chain_marks, barcode_graphics_quality)

def is_roll_status_supported(printer_name: str) -> bool:
    """Returns if the provided printer belongs to the 550 series.
    
    Args:
        :printer_name (str): The name of the printer.
    """
    return __printer_manager.IsRollStatusSupported(printer_name)

def get_roll_status(printer_name : str) -> RollStatus:
    """Returns the number of labels remaining.

    Returns the number of labels remaining on the roll if rollstatus is supported. To update this number you must run refresh_connection() or refresh_printer().

    Args:
        :printer_name (str): The name of the printer.
    """
    return RollStatus(__printer_manager.GetRollStatusInPrinter(printer_name).Result)

def refresh_printer(printer_name: str):
    """Refreshes the printer connection
    
    Note that this is done asynchronously and we recommend sleeping for a small amount of time if the results are required immediately."""
    __printer_manager.GetPrinterStatus(printer_name)
