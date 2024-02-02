#!/bin/bash

make_tar_and_move_to_setup (){
  echo "make_tar_and_move_to_setup"
  
  sh create-cras-tar.sh
  cp cras.tar ../setup_template/data/app_cras

  sh create-check_cras_script_runner-tar.sh
  cp check_cras_script_runner.tar ../setup_template/data/app_cras  
  
  cp version.txt ../setup_template
  cp Release_Note.txt ../setup_template
  cp AcquisitionFileConverter.jar ../setup_template/data/app_cras

  echo "make_tar_and_move_to_setup finish"
}

copy_all_setup_to_package_files () {
  echo "copy all to package"
  
  rm -rf package
  mkdir package
  cp -r ../setup_template/* package
  
  echo "copy all to package finish"
}

zip_package () {
  echo "make setup zip file"
  
  version=$(cat version.txt)

  version=$(echo "$version" | sed 's/\./_/g')
  
  rm -rf setup_Cras_Server_Ver_$version.zip
  rm -rf setup_Cras_Server_Ver_$version
  
  package_name=setup_Cras_Server_Ver_$version
  mv package $package_name
  
  # ./7zz a setup_Cras_Server_Ver_$version.zip $package_name
  7za a setup_Cras_Server_Ver_$version.zip $package_name
  
  rm -rf $package_name
  
  echo "make setup zip file finish"
}

make_tar_and_move_to_setup
copy_all_setup_to_package_files
zip_package

echo Finish
