-- Zync render menu extension script
macroScript RenderWithZync
category: "Menu Rendering"
tooltip: "Render with Zync"
(
  on execute do
  (
    local maxScriptPath = getThisScriptFilename()
    local pythonScriptPath = substituteString maxScriptPath "Zync.ms" "zync_3dsmax.py"
    python.ExecuteFile pythonScriptPath
  )
)

if menuMan.registerMenuContext 0x3c0c52e7 then
(
  local renderMenuItem
  local mainMenuBar = menuMan.getMainMenuBar()
  for i = 1 to mainMenuBar.numItems() do
  (
    local menuItem = mainMenuBar.getItem(i)
    if menuItem.getTitle() == "&Rendering" then
    (
      renderMenuItem = mainMenuBar.getItem(i)
      exit
    )
  )
  local renderMenu = renderMenuItem.getSubMenu()
  local newAction = menuMan.createActionItem "RenderWithZync" "Menu Rendering"
  for i = 1 to renderMenu.numItems() do
  (
    local menuItem = renderMenu.getItem(i)
    if menuItem.getTitle() == "Render" then
    (
      renderMenu.addItem newAction (i + 1)
      exit
    )
  )
  menuMan.updateMenuBar()
)
