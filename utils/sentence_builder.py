class SentenceBuilder:

    def __init__(self):
        self.sequence = []

    # 🔥 supports batch input (used by live.py)
    def build_from_words(self, words):
        self.sequence = words
        return self.build()

    def add(self, sign):
        if sign is None:
            return None

        self.sequence.append(sign)

        if len(self.sequence) > 5:
            self.sequence.pop(0)

        return self.build()

    def build(self):
        s = self.sequence

        if "Nilalagnat Ako" in s and "Nahihilo" in s:
            return "Ako ay may lagnat at nahihilo."

        if "Nilalagnat Ako" in s and "Nagsusuka" in s:
            return "May lagnat ako."
        
        if "Nilalagnat" in s and "Inuubo Ako" in s:
            return "Nilalagnat at inuubo rin ako."

        if "Panlalabo ng mata" in s and "Kahapon" in s:
            return "Nagsimula ang panlalabo ng mata ko kahapon."
        
        if "Pananakit ng ulo" in s and "Nahihilo" in s:
            return "Masakit ang aking ulo at nahihilo rin ako."

        if "Inuubo Ako" in s and "Nagsusuka" in s:
            return "Inuubo ako at nagsusuka."
        
        if "Nasusuka" in s and "Pagdudumi" in s:
            return "Nagsusuka at nagdudumi ako."
        
        if "Magandang Umaga" in s and "Pagdurugo" in s:
            return "Napansin ko ang pagdurugo kaninang umaga."
        
        if "Mabagal" in s and "Pagdudumi" in s:
            return "Mabagal ang aking pagdudumi."
        
        if "Mabilis" in s and "Namamawis" in s:
            return "Mabilis ang tibok ng puso ko at namamawis ako."
        
        if "Mabilis" in s and "Kahapon" in s:
            return "Mabilis po ang aking paghinga simula kahapon."
        
        if "Mabilis" in s and "Kapos sa paghinga" in s:
            return "Mabilis ang tibok ng puso ko at kapos sa paghinga."
        
        if "Magandang umaga" in s and "Ikinagagalak kong makilala ka" in s:
            return "Magandang umaga, ikinagagalak kong makilala ka Doc."
        
        if "Magandang hapon" in s and "Ikinagagalak kong makilala ka" in s:
            return "Magandang hapon, ikinagagalak kong makilala ka Doc."
        
        if "Magandang hapon" in s and "Inuubo" in s and "Kahapon" in s:
            return "Magandang hapon po, inuubo po ako simula pa kahapon."
        
        if "Ikinagagalak kong makilala ka" in s and "Okay" in s and "Ako" in s:
            return "Ikinagagalak kong makilala ka, Doc. Okay lang po ako."
        
        if "Sinisipon" in s and "Impeksyon" in s:
            return "Sinisipon po ako at may kasamang impeksyon sa lalamunan."
        
        if "Sinisipon" in s and "Pananakit ng ulo" in s:
            return "Sinisipon po ako at may kasamang pananakit ng ulo."
        
        if "Oo" in s and "Panunuyo ng bibig" in s:
            return "Opo, may nararamdaman akong panunuyo ng bibig."
        
        if "Hindi" in s and "Masakit ulo" in s:
            return "Hindi masakit ulo ko."
        
        if "Hindi" in s and "Alerhiya" in s:
            return "Hindi po, wala akong alerhiya sa kahit ano."

        if "Salamat" in s and "Naiintindihan" in s:
            return "Salamat, Naiintindihan ko po ang bilin niyo."
        
        if "Salamat" in s and "Alam" in s:
            return "Salamat po, alam ko na po."
        
        if "Ako" in s and "Hindi" in s and "Alerhiya" in s:
            return "Wala akong alerhiya."

        if "Hello" in s and "Magandang umaga" in s:
            return "Hello, Magandang umaga."
        
        if "Hello" in s and "Magandang hapon" in s:
            return "Hello, Magandang hapon."
        
        if "Nahihilo" in s and "Impeksyon" in s:
            return "Nahihilo ako at masakit ang kasukasuan ko, Sir Ricrey."
        
        if "Nanay" in s and "Tatay" in s:
            return "Tanging Ina at Ama ko, uuwi na po ako."

        return " ".join(s)