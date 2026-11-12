import { Component, computed, input } from '@angular/core';

const docsRoot = "https://docs.godotengine.org/en/latest/";

@Component({
  selector: 'app-badges',
  imports: [],
  templateUrl: './badges.html',
  styleUrl: './badges.css',
})

export class Badges {
  fileName = input<string>("N/A");

  protected readonly source = computed(() => {
    // Stored paths end in "/clean_html/<doc path>". The docs site serves that doc path.
    const normalized = this.fileName().replaceAll("\\", "/");
    const marker = "/clean_html";
    const index = normalized.indexOf(marker);
    const label = index === -1
      ? normalized.replace(/^\/+/, "")
      : normalized.slice(index + marker.length).replace(/^\/+/, "");
    return { label, href: docsRoot + label };
  });
}
