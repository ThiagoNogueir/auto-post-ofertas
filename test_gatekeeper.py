"""
Comprehensive verification test for src.services.gatekeeper
"""
import sys
from src.services.gatekeeper import (
    validate_deal_for_whatsapp_group,
    GROUP_TECH,
    GROUP_CASA,
    GROUP_BELEZA,
    GROUP_MERCADO,
    GROUP_MODA,
    GROUP_PETS,
    GROUP_BEBES,
    GROUP_AUTO
)

test_suite = [
    # 1. MODA Group tests
    ("Vestido Midi Três Marias Viscose Linho Com Bolsos Laterais", GROUP_MODA, True, "Real dress should pass Moda"),
    ("Camisa Polo Masculina Slim Fit Algodão", GROUP_MODA, True, "Real shirt should pass Moda"),
    ("Tênis Nike Air Force 1 07 Masculino Branco", GROUP_MODA, True, "Real sneakers should pass Moda"),
    ("Omega Plus 240 Caps Dark Lab", GROUP_MODA, False, "Omega 3 must be blocked from Moda"),
    ("Whey Isolate Protein Fuse Refil 1,8kg Dark Lab", GROUP_MODA, False, "Whey must be blocked from Moda"),
    ("Creatina Monohidratada 100% Pura 300g Max Titanium", GROUP_MODA, False, "Creatine must be blocked from Moda"),
    ("Furadeira e Parafusadeira Bosch 12V", GROUP_MODA, False, "Power tools must be blocked from Moda"),
    ("Ração Premier Pet Cães Adultos 15kg", GROUP_MODA, False, "Pet food must be blocked from Moda"),
    ("Placa de Vídeo RTX 4060 8GB GDDR6", GROUP_MODA, False, "GPU must be blocked from Moda"),
    ("Vestido Bebê Menina Malha Waffle Manga Longa Blue 6-9m", GROUP_MODA, False, "Baby dress must be blocked from Moda"),
    ("Trampolim Jump Profissional Com Capa Saia Diâmetro 1 M 200kg Preto", GROUP_MODA, False, "Trampoline with capa saia must be blocked from Moda"),
    ("Mesa Multijogos 10 em 1 Ahead Sports Azul Pebolim Bilhar Air Hockey Tênis de Mesa Xadrez com Acessórios", GROUP_MODA, False, "Multi-game table must be blocked from Moda"),
    ("Saia Box Casal Matelada Ultrassônica Branca", GROUP_MODA, False, "Bed skirt must be blocked from Moda"),
    ("Raquete de Tênis de Mesa Ping Pong Vollo", GROUP_MODA, False, "Table tennis racket must be blocked from Moda"),

    # 2. CASA & DECORAÇÃO Group tests
    ("Fritadeira Sem Óleo Air Fryer Mondial 4L Inox", GROUP_CASA, True, "Air fryer should pass Casa"),
    ("Jogo De Toalhas Banhão 5 Peças 100% Algodão", GROUP_CASA, True, "Towels should pass Casa"),
    ("Vestido Midi Três Marias Viscose Linho Com Bolsos", GROUP_CASA, False, "Dress must be blocked from Casa"),
    ("Relógio Smartwatch Basike W88 Pro Max Esportivo 47mm", GROUP_CASA, False, "Smartwatch must be blocked from Casa"),
    ("Whey Protein 100% Concentrado 900g", GROUP_CASA, False, "Whey must be blocked from Casa"),
    ("Placa de Vídeo RTX 4070 Ti 12GB", GROUP_CASA, False, "GPU must be blocked from Casa"),
    ("Cueca Boxer Sem Costura Lupo Kit com 10", GROUP_CASA, False, "Underwear must be blocked from Casa"),

    # 3. TECNOLOGIA & GAMES Group tests
    ("Relógio Smartwatch Basike W88 Pro Max Esportivo 47mm", GROUP_TECH, True, "Smartwatch should pass Tech"),
    ("Console PlayStation 5 Slim 1TB com 2 Jogos", GROUP_TECH, True, "PS5 should pass Tech"),
    ("Smartphone Samsung Galaxy S24 Ultra 256GB", GROUP_TECH, True, "Smartphone should pass Tech"),
    ("Vestido Longo Estampado Floral", GROUP_TECH, False, "Dress must be blocked from Tech"),
    ("Cerveja Heineken Lata 350ml Pack 12 unidades", GROUP_TECH, False, "Beer must be blocked from Tech"),

    # 4. MERCADO & BEBIDAS Group tests
    ("Omega Plus 240 Caps Dark Lab", GROUP_MERCADO, True, "Omega 3 should pass Mercado"),
    ("Whey Isolate Protein Fuse Refil 1,8kg Dark Lab", GROUP_MERCADO, True, "Whey should pass Mercado"),
    ("Vinho Chileno Casillero del Diablo Cabernet Sauvignon 750ml", GROUP_MERCADO, True, "Wine should pass Mercado"),
    ("Azeite de Oliva Extra Virgem Andorinha 500ml", GROUP_MERCADO, True, "Olive oil should pass Mercado"),
    ("Vestido Midi Floral", GROUP_MERCADO, False, "Dress must be blocked from Mercado"),
    ("Smartphone Xiaomi Redmi Note 13 128GB", GROUP_MERCADO, False, "Phone must be blocked from Mercado"),
    ("Bicicleta Ergométrica Spinning Inércia 5kg Velocron V500 Preto", GROUP_MERCADO, False, "Spinning bike must be blocked from Mercado"),
    ("Bicicleta Ergométrica Spinning Inércia 5kg Velocron V500 Preto", GROUP_MODA, False, "Spinning bike must be blocked from Moda"),
    ("Bicicleta Ergométrica Spinning Inércia 5kg Velocron V500 Preto", GROUP_CASA, False, "Spinning bike must be blocked from Casa"),

    # 5. PET SHOP Group tests (Strict positive requirement)
    ("Ração Royal Canin Golden Retriever Adulto 15kg", GROUP_PETS, True, "Pet food should pass Pet Shop"),
    ("Arranhador para Gatos com Casinha e Rede", GROUP_PETS, True, "Cat tree should pass Pet Shop"),
    ("Antipulgas Simparic 20mg para Cães", GROUP_PETS, True, "Pet meds should pass Pet Shop"),
    ("Churrasqueira Portátil a Carvão", GROUP_PETS, False, "Non-pet item must be blocked from Pet Shop"),
    ("Vestido Feminino Estampado", GROUP_PETS, False, "Non-pet item must be blocked from Pet Shop"),

    # 6. BEBÊS & BRINQUEDOS Group tests
    ("Fralda Pampers Confort Sec Mega G 72 Tiras", GROUP_BEBES, True, "Diapers should pass Bebês"),
    ("Boneca Barbie Fashionista Vestido Rosa", GROUP_BEBES, True, "Barbie should pass Bebês"),
    ("Vestido Bebê Menina Malha Waffle Manga Longa Blue 6-9m", GROUP_BEBES, True, "Baby dress should pass Bebês"),
    ("Cerveja Corona Extra 330ml Pack com 6", GROUP_BEBES, False, "Alcohol must be blocked from Bebês"),
    ("Whey Protein Dark Lab", GROUP_BEBES, False, "Adult supplements must be blocked from Bebês"),

    # 7. FERRAMENTAS & AUTOMOTIVO Group tests
    ("Jogo de Chaves Combinadas Vonder 12 peças", GROUP_AUTO, True, "Tools should pass Auto"),
    ("Pneu Aro 14 Pirelli Cinturato 175/65R14", GROUP_AUTO, True, "Tire should pass Auto"),
    ("Vestido Festa Longo Sereia", GROUP_AUTO, False, "Dress must be blocked from Auto"),
    ("Batom Líquido Matte Maybelline", GROUP_AUTO, False, "Makeup must be blocked from Auto")
]

failed = 0
for title, group, expected_allow, description in test_suite:
    allowed, reason = validate_deal_for_whatsapp_group(group, title)
    status = "PASS" if allowed == expected_allow else "FAIL"
    if status == "FAIL":
        failed += 1
        print(f"[FAIL] {description}\n   Title: '{title}'\n   Expected: {expected_allow}, Got: {allowed} | Reason: {reason}")
    else:
        print(f"[OK] {description} -> {reason}")

print(f"\n==========================================")
print(f"Results: {len(test_suite) - failed}/{len(test_suite)} passed.")
if failed == 0:
    print("ALL GATEKEEPER TESTS PASSED WITH 100% PRECISION!")
else:
    print(f"FAILED {failed} TESTS.")
    sys.exit(1)
