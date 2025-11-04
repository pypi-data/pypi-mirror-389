import glob
import os
import shutil
import platform
import subprocess
from pathlib import Path
import sysconfig
import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

def clean_folder(folder):
    files = glob.glob(folder + "/*")
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
        else:
            if not (os.path.basename(f) == "Mac" or os.path.basename(f) == "Win"):
                shutil.rmtree(f)

def copy_files(fromPath, toPath, files, bads = [], bad_word = ""):
    for f in files:
        if f not in bads and (bad_word == "" or bad_word not in f):
            shutil.copy(fromPath + "/" + f, toPath)

def glob_and_copy(from_path, to_path, pattern):
    files_globbed = glob.glob(pattern, root_dir=from_path)
    copy_files(from_path, to_path, files_globbed)

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        platform_config = sysconfig.get_platform()
        dlls_path = "dymo_sdk/dlls"
        curr_file = Path(self.directory).parent.resolve()
        if "platform" in os.environ and os.environ["platform"] != "":
            chosen_plat = os.environ["platform"]
        else:
            chosen_plat = platform.system()
        if "arch" in os.environ and os.environ["arch"] != "":
            arch = os.environ["arch"]
        else:
            arch = ""
        
        #If we're calling from the build agent, the build agent will automatically build on it's own
        skip_dot_net_build = ("run_from_agent" in os.environ and os.environ["run_from_agent"] == "true")
        
        if chosen_plat == "Windows":
            #Windows
            #path to projects for building
            successful = True
            sdk_dlls = curr_file.parent / "DymoSDK" / "bin" / "Release" / "net8.0-windows10.0.19041.0"
            sdk_dlls = str(sdk_dlls.resolve())

            label_api_dlls = curr_file.parent.parent / "Components" / "DYMO.LabelAPI.Windows" / "bin" / "x64" / "Release" / "net8.0-windows10.0.19041.0" / "win-x64"
            label_api_dlls = str(label_api_dlls.resolve())


            if not skip_dot_net_build:
                sdk_path = curr_file.parent / "DymoSDK" / "DymoSDK.csproj"
                sdk_path = str(sdk_path.resolve())
                label_api_win_path = curr_file.parent.parent / "Components" / "DYMO.LabelAPI.Windows" / "DYMO.LabelAPI.Windows.csproj"
                label_api_win_path = str(label_api_win_path.resolve())

                inter_folder1 = ""
                inter_folder2 = ""
                if arch == "":
                    if "arm64" in platform_config:
                        inter_folder1 = "arm64"
                        inter_folder2 = "win-arm64"
                    elif "amd64" in platform_config:
                        inter_folder1 = "x64"
                        inter_folder2 = "win-x64"
                    elif "win32" in platform_config:
                        inter_folder1 = "x86"
                        inter_folder2 = "win-x86"
                else:
                    if arch == "arm64":
                        inter_folder1 = "arm64"
                        inter_folder2 = "win-arm64"
                    elif arch == "x64":
                        inter_folder1 = "x64"
                        inter_folder2 = "win-x64"
                    elif arch == "x86":
                        inter_folder1 = "x86"
                        inter_folder2 = "win-x86"

                #path to dlls
                bin_path_sdk = curr_file.parent / "DymoSDK" / "bin" / "Release" / "net8.0-windows10.0.19041.0"
                bin_path_sdk = str(bin_path_sdk.resolve())
                bin_path_label_api = curr_file.parent.parent / "Components" / "DYMO.LabelAPI.Windows" /"bin" / inter_folder1 / "Release" / "net8.0-windows10.0.19041.0" / inter_folder2
                bin_path_label_api = str(bin_path_label_api.resolve())

                clean_command = ["dotnet", "clean", sdk_path]
                build_command = ["dotnet", "build", sdk_path, "-c", "Release"]
                clean_command_win = ["dotnet", "clean", label_api_win_path]
                build_command_win = ["dotnet", "build", label_api_win_path, "-c",  "Release", "--arch", inter_folder1]

                try:
                    dotnet_clean_result = subprocess.run(clean_command, check=True, capture_output=True, text=True, shell=True)
                    dotnet_build_result = subprocess.run(build_command, check=True, capture_output=True, text=True, shell=True)
                    dotnet_clean_result_win = subprocess.run(clean_command_win, check=True, capture_output=True, text=True, shell=True)
                    dotnet_build_result_win = subprocess.run(build_command_win, check=True, capture_output=True, text=True, shell=True)
                except subprocess.CalledProcessError as e:
                    print(f"Ran into error: {e}")
                    print(e.stdout)
                    print("now printing errors")
                    print(e.stderr)
                    successful = False
                    #raise e
            
            #copy the required files
            if successful:
                clean_folder(dlls_path)
                glob_and_copy(sdk_dlls, dlls_path, "*.dll")
                glob_and_copy(label_api_dlls, dlls_path, "*.dll")
                print("successfully copied dlls")
            else:
                print("did not copy new dlls")
        else:
            #Mac
            successful = True
            sdk_path = curr_file.parent / "DymoSDK" / "DymoSDK.csproj"
            sdk_path = str(sdk_path.resolve())
            
            label_api_mac_path = curr_file.parent.parent / "Components" / "DYMO.LabelAPI.Mac" / "DYMO.LabelAPI.Mac.csproj"
            label_api_mac_path = str(label_api_mac_path.resolve())

            bin_path_sdk = curr_file.parent / "DymoSDK" / "bin" / "Release" / "netstandard2.0"
            bin_path_sdk = str(bin_path_sdk.resolve())
            bin_path_label_api = curr_file.parent.parent / "Components" / "DYMO.LabelAPI.Mac" / "bin" / "Release" / "net8.0-macos"
            bin_path_label_api = str(bin_path_label_api.resolve())

            if not skip_dot_net_build:
                clean_command = ["dotnet clean " + sdk_path]
                build_command = ["dotnet build " + sdk_path + " --configuration Release"]
                clean_command_2 = ["dotnet clean " + label_api_mac_path]
                build_command_2 = ["dotnet build " + label_api_mac_path + " --configuration Release"]
                try:
                    dotnet_clean_result = subprocess.run(clean_command, check=True, capture_output=True, text=True, shell=True)
                    dotnet_build_result = subprocess.run(build_command, check=True, capture_output=True, text=True, shell=True)
                    dotnet_clean_result_2 = subprocess.run(clean_command_2, check=True, capture_output=True, text=True, shell=True)
                    dotnet_build_result_2 = subprocess.run(build_command_2, check=True, capture_output=True, text=True, shell=True)
                except subprocess.CalledProcessError as e:
                    print(f"Ran into error: {e}")
                    print(e.stdout)
                    print("now printing errors")
                    print(e.stderr)
                    successful = False
                    #raise e
            
            #copy the required files
            if platform.system() == "Windows":
                native_build_command = ["./build.native.osx.arm64.sh"]
            else:
                native_build_command = ["source build.native.osx.arm64.sh"]
            try:
                build_native_result = subprocess.run(native_build_command, check=True, capture_output=True, text=True, shell=True, cwd="../../Components.Native")
            except subprocess.CalledProcessError as e:
                    print(f"Ran into error: {e}")
                    print(e.stdout)
                    print("now printing errors")
                    print(e.stderr)
            if successful:
                clean_folder(dlls_path)
                glob_and_copy(bin_path_sdk, dlls_path, "*.dll")
                glob_and_copy(bin_path_sdk, dlls_path, "*.a")
                glob_and_copy(bin_path_sdk, dlls_path, "*.dylib")

                glob_and_copy(label_api_mac_path, dlls_path, "*.dll")
                glob_and_copy(label_api_mac_path, dlls_path, "*.a")
                glob_and_copy(label_api_mac_path, dlls_path, "*.dylib")

                native_path = "../../native/osx/dylib/Release"
                glob_and_copy(native_path, dlls_path, "*.dylib")
                mac_os_native_skiasharp = str(Path.home().resolve()) + "/.nuget/packages/skiasharp.nativeassets.macos/3.116.1/runtimes/osx/native/libSkiaSharp.dylib"
                os.makedirs(dlls_path + "/@rpath/libSkiaSharp.framework", exist_ok=True)
                #copy to both original folder, and rpath folder since sometimes it looks at one or the other
                shutil.copy(mac_os_native_skiasharp, dlls_path)
                shutil.copy(mac_os_native_skiasharp, dlls_path + "/@rpath/libSkiaSharp.framework")

                #grab framework file
                if platform.system() == "Windows":
                    #hope 9.0 works, else we will need to install 8.0 onto our build agent
                    mac_os_dll_path - "Program Files/dotnet/packs/Micrososft.macOS.Runtime.osx-arm64.net9.0_15.0/15.5.9219/runtimes/osx-arm64/lib/net9.0/Microsoft.macOS.dll"
                else:
                    mac_os_dll_path = "/usr/local/share/dotnet/packs/Microsoft.macOS.Runtime.osx-arm64.net8.0_15.0/15.0.8319/runtimes/osx-arm64/lib/net8.0/Microsoft.macOS.dll"
                
                shutil.copy(mac_os_dll_path, dlls_path)

                print("successfully copied dlls")


        #set build tags
        build_data["infer_tag"] = False

        build_data["pure_python"] = False

        if platform.system() == "Windows":
            platform_tag = platform_config.replace("-", "_").replace(".","_")
            if arch == "arm64":
                platform_tag = platform_tag.replace("amd64", "arm64")
            elif arch == "x86":
                platform_tag = platform_tag.replace("win_amd64", "win32")
            print(f"platform_tag:{platform_tag}")
        else:
            platform_tag = "macosx_13_0_arm64"
        
        abi_tag = "none"
        python_tag = "py2.py3"

        build_data["tag"] = python_tag + "-" + abi_tag + "-" + platform_tag