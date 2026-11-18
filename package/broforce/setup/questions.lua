-- SPDX-License-Identifier: MIT
-- SPDX-FileCopyrightText: 2026 Ronax

local questions = {
    {
        id = "TEXTURE_QUALITY",
        question = "Texture compression quality? Sharper takes longer to set up.",
        options = {
            { "fastest", "Fast (recommended)" },
            { "medium", "Sharper" },
        },
    },
    {
        id = "RESOLUTION",
        question = "Render resolution? Lower settings draw fewer pixels and scale the picture to the screen. Change this later in resolution.txt.",
        options = {
            { "auto", "Automatic (recommended): 50% on 1 GB ARM64, otherwise 75%" },
            { "0.5", "50% of device resolution" },
            { "0.75", "75% of device resolution" },
            { "0.833", "83% of device resolution" },
            { "device", "Device resolution" },
        },
    },
    {
        id = "BUTTONS",
        question = "Which letters are on your handheld's buttons? This changes the labels in Controls. Change this later in buttons.txt.",
        options = {
            { "nintendo", "Nintendo: B at the bottom (recommended)" },
            { "xbox", "Xbox: A at the bottom" },
        },
    },
}

local w = tonumber(os.getenv("DISPLAY_WIDTH"))
local h = tonumber(os.getenv("DISPLAY_HEIGHT"))
local aspect = w and h and h > 0 and w / h
local shapes = { { "fill", "Fill the screen (recommended)" } }
for _, shape in ipairs({
    { "16:9", 16 / 9 }, { "4:3", 4 / 3 }, { "1:1", 1 },
}) do
    if not aspect or math.abs(aspect - shape[2]) > 0.015 then
        table.insert(shapes, { shape[1], shape[1] .. " with black bars" })
    end
end
table.insert(questions, 2, {
    id = "ASPECT",
    question = "Picture shape? Fit the handheld or choose a fixed shape with black bars. Change this later in aspect.txt.",
    options = shapes,
})
return questions
