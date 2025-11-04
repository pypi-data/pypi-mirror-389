from bluer_objects import README
from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.consts import assets2
from bluer_sbc.README.design import design_doc

image_template = assets2 + "nafha/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "nafha",
            "marquee": image_template.format("01.png"),
            "url": "./bluer_sbc/docs/nafha",
        }
    ]
)

items = ImageItems(
    {
        image_template.format(f"{filename}"): ""
        for filename in [
            f"{index+1:02}.png"
            for index in range(
                4,
            )
        ]
        + [
            "20251028_123428.jpg",
            "20251028_123438.jpg",
        ]
    },
)

docs = [
    design_doc(
        "nafha",
        items,
        own_folder=True,
    ),
    {
        "path": "../docs/nafha/parts-v1.md",
    },
]
