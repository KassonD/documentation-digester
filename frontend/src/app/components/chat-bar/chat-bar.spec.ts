import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ChatBar } from './chat-bar';

describe('ChatBar', () => {
  let component: ChatBar;
  let fixture: ComponentFixture<ChatBar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatBar]
    })
      .compileComponents();

    fixture = TestBed.createComponent(ChatBar);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
